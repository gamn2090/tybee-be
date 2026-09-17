# Cambios aplicados — Admin / Backend Issues

Este documento detalla, punto por punto según la lista reportada por el cliente, qué se implementó, en qué archivo, y el código exacto que se agregó o modificó. Se aplicaron migraciones y se corrió `python manage.py check` sin errores; el servidor de desarrollo recargó los cambios sin excepciones.

Archivos nuevos:
- [`tybee_backend/search_utils.py`](tybee_backend/search_utils.py)
- [`local_places/migrations/0028_category_is_active_alter_cartmap_description_and_more.py`](local_places/migrations/0028_category_is_active_alter_cartmap_description_and_more.py)
- [`rules/migrations/0004_alter_rule_description.py`](rules/migrations/0004_alter_rule_description.py)

Archivos modificados:
- [`local_places/models.py`](local_places/models.py)
- [`local_places/views.py`](local_places/views.py)
- [`local_places/admin.py`](local_places/admin.py)
- [`local_places/static/local_places/js/admin_places.js`](local_places/static/local_places/js/admin_places.js)
- [`rules/models.py`](rules/models.py)
- [`rules/views.py`](rules/views.py)
- [`rules/admin.py`](rules/admin.py)

---

## 1. Búsqueda en Admin (spelling, puntuación, parciales, dropdown de sugerencias)

**Antes:** Django Admin usa `search_fields` con `LIKE %term%` exacto sobre uno o dos campos. No tolera errores de tipeo ni diferencias de puntuación, y no ofrece autocompletado.

**Qué se hizo:**

1. Se creó un helper de búsqueda reutilizable en `tybee_backend/search_utils.py`, con normalización de texto (minúsculas, sin puntuación/espacios) y coincidencia difusa vía `difflib.SequenceMatcher`:

```python
# tybee_backend/search_utils.py
import re
from difflib import SequenceMatcher

_NON_ALNUM_RE = re.compile(r"[^a-z0-9]+")


def normalize_text(text):
    """Lowercase and strip everything but letters/digits."""
    return _NON_ALNUM_RE.sub("", (text or "").lower())


def fuzzy_match(query, target, threshold=0.6):
    """True if `query` is a (normalized) substring of `target`, or close
    enough to it (spelling variations) per `SequenceMatcher` ratio."""
    normalized_query = normalize_text(query)
    normalized_target = normalize_text(target)
    if not normalized_query or not normalized_target:
        return False
    if normalized_query in normalized_target:
        return True
    return SequenceMatcher(None, normalized_query, normalized_target).ratio() >= threshold


class FuzzySearchAdminMixin:
    """Mixin para `unfold.admin.ModelAdmin` que reemplaza la búsqueda
    estándar por una tolerante a puntuación y errores de tipeo."""

    fuzzy_search_threshold = 0.6

    def get_search_haystack(self, obj):
        return [str(obj)]

    def get_search_results(self, request, queryset, search_term):
        search_term = (search_term or "").strip()
        if not search_term:
            return queryset, False

        tokens = search_term.split()
        matched_ids = []
        for obj in queryset:
            haystacks = [h for h in self.get_search_haystack(obj) if h]
            if all(
                any(fuzzy_match(token, h, self.fuzzy_search_threshold) for h in haystacks)
                for token in tokens
            ):
                matched_ids.append(obj.pk)

        return queryset.filter(pk__in=matched_ids), False
```

2. Se aplicó `FuzzySearchAdminMixin` a **todos** los `ModelAdmin` relevantes: `LocalPlaceAdmin`, `CategoryAdmin`, `TagAdmin`, `ActivityAdmin`, `LiveLikeALocalAdmin`, `CartMapAdmin` (en `local_places/admin.py`) y `RuleAdmin`, `RuleCategoryAdmin` (en `rules/admin.py`). Cada uno define `get_search_haystack()` indicando qué campos (incluyendo relaciones, como categoría/tags/actividades) se buscan.

   Ejemplo en `LocalPlaceAdmin` (busca por nombre, dirección, teléfono, categoría, tags y actividades — no solo el nombre):

```python
def get_search_haystack(self, obj):
    return [
        obj.name,
        obj.address,
        obj.contact_number,
        obj.category.title if obj.category else "",
        " ".join(t.title for t in obj.tags.all()),
        " ".join(a.title for a in obj.activities.all()),
    ]

def get_search_results(self, request, queryset, search_term):
    queryset = queryset.select_related("category").prefetch_related(
        "tags", "activities"
    )
    return super().get_search_results(request, queryset, search_term)
```

3. **Dropdown de sugerencias** (implementado para el listado de Local Places, el más pedido — ver ejemplo "Restaurants" del cliente):
   - Nuevo endpoint AJAX en `LocalPlaceAdmin` (`local_places/admin.py`):

```python
def get_urls(self):
    urls = super().get_urls()
    custom_urls = [
        path(
            "search-suggestions/",
            self.admin_site.admin_view(self.search_suggestions_view),
            name="local_places_localplace_search_suggestions",
        ),
    ]
    return custom_urls + urls

def search_suggestions_view(self, request):
    """Backs the dropdown suggestions list under the changelist search box."""
    query = (request.GET.get("q") or "").strip()
    if not query:
        return JsonResponse({"results": []})

    queryset = self.get_queryset(request).select_related("category")
    results = []
    for obj in queryset:
        haystacks = self.get_search_haystack(obj)
        if any(fuzzy_match(query, h, self.fuzzy_search_threshold) for h in haystacks if h):
            results.append(
                {
                    "id": obj.pk,
                    "name": obj.name,
                    "category": obj.category.title if obj.category else "",
                }
            )
        if len(results) >= 8:
            break
    return JsonResponse({"results": results})
```

   - Nuevo bloque de JS en `local_places/static/local_places/js/admin_places.js` (agregado al final del archivo, sin tocar el código existente de Google Places/validación de imágenes) que engancha el input de búsqueda del changelist (`#searchbar`), hace `fetch` con debounce de 200ms al endpoint de arriba, y renderiza un dropdown posicionado bajo el input; al hacer click en una sugerencia, completa el campo y envía el formulario:

```javascript
// ─── Search suggestions dropdown (Admin issue #1) ─────────────────────────────
(function () {
    function init() {
        var input = document.getElementById("searchbar");
        if (!input || input.dataset.suggestionsAttached) return;
        input.dataset.suggestionsAttached = "1";

        var suggestUrl = window.location.pathname.replace(/\/?$/, "/") + "search-suggestions/";
        var wrapper = input.closest("#toolbar") || input.parentNode;
        wrapper.style.position = wrapper.style.position || "relative";

        var dropdown = document.createElement("div");
        dropdown.id = "lp-search-suggestions";
        dropdown.style.cssText =
            "display:none;position:absolute;z-index:1000;background:#fff;" +
            "border:1px solid #d1d5db;border-radius:8px;box-shadow:0 8px 24px rgba(0,0,0,0.12);" +
            "max-height:260px;overflow-y:auto;min-width:240px;margin-top:4px;";
        wrapper.appendChild(dropdown);

        function positionDropdown() {
            var rect = input.getBoundingClientRect();
            var wrapperRect = wrapper.getBoundingClientRect();
            dropdown.style.left = (rect.left - wrapperRect.left) + "px";
            dropdown.style.top = (rect.bottom - wrapperRect.top) + "px";
            dropdown.style.width = rect.width + "px";
        }

        function hideDropdown() {
            dropdown.style.display = "none";
        }

        function renderResults(results) {
            dropdown.innerHTML = "";
            if (!results.length) {
                hideDropdown();
                return;
            }
            results.forEach(function (item) {
                var row = document.createElement("div");
                row.textContent = item.category ? item.name + "  —  " + item.category : item.name;
                row.style.cssText =
                    "padding:8px 12px;cursor:pointer;font-size:13px;color:#111827;";
                row.addEventListener("mouseenter", function () {
                    row.style.background = "#f3f4f6";
                });
                row.addEventListener("mouseleave", function () {
                    row.style.background = "transparent";
                });
                row.addEventListener("mousedown", function (e) {
                    // mousedown (not click) so it fires before the input's blur
                    e.preventDefault();
                    input.value = item.name;
                    hideDropdown();
                    input.form.submit();
                });
                dropdown.appendChild(row);
            });
            positionDropdown();
            dropdown.style.display = "block";
        }

        var debounceTimer = null;
        var currentController = null;

        input.addEventListener("input", function () {
            var query = input.value.trim();
            clearTimeout(debounceTimer);
            if (!query) {
                hideDropdown();
                return;
            }
            debounceTimer = setTimeout(function () {
                if (currentController) currentController.abort();
                currentController = new AbortController();
                fetch(suggestUrl + "?q=" + encodeURIComponent(query), {
                    signal: currentController.signal,
                    credentials: "same-origin",
                })
                    .then(function (res) {
                        return res.ok ? res.json() : { results: [] };
                    })
                    .then(function (data) {
                        renderResults(data.results || []);
                    })
                    .catch(function () {
                        /* ignore aborted/failed requests */
                    });
            }, 200);
        });

        input.addEventListener("blur", function () {
            setTimeout(hideDropdown, 150);
        });

        window.addEventListener("resize", positionDropdown);
    }

    window.addEventListener("load", init);
})();
```

**Resultado:** buscar "Restaurent" (mal escrito) encuentra "Restaurant"; "OLearys" encuentra "O'Leary's"; se puede buscar por categoría/tag/actividad, no solo el nombre; y aparece un dropdown con hasta 8 sugerencias en vivo mientras se tipea (en el listado de Local Places).

**Limitación honesta:** el dropdown de sugerencias solo se implementó para el listado de **Local Places** (el caso de uso mencionado por el cliente). Extenderlo a Categories/Tags/Rules es trivial (mismo patrón) — se puede agregar si se necesita. La búsqueda difusa de texto (sin dropdown) sí quedó activa en **todos** los listados mencionados arriba.

**Status:** ✅ Implementado (antes: "Pending / Additional backend effort").

---

## 2. Quitar paginación del Admin

No requirió cambios — ya estaba resuelto en el código existente (`list_per_page = 10000` en todos los `ModelAdmin`). Se verificó y se mantiene.

**Status:** ✅ Ya resuelto (confirmado, sin cambios).

---

## 3. Tags vs. Activities

**Diagnóstico:** técnicamente hay redundancia — `Tag` es solo un título; `Activity` tiene título + descripción + su propio M2M a `Tag`; y `LocalPlace` tiene M2M directo a ambos. Esto es una decisión de producto pendiente que no puedo resolver por vos (necesita definición del cliente sobre el caso de uso real).

**Qué sí se hizo — paridad técnica de búsqueda/filtrado** (para que, mientras se define el modelo de negocio, ambos funcionen igual):

- `ActivityAdmin` ahora tiene `autocomplete_fields = ("tags",)` y muestra una columna `tag_list` en el listado, igual que ya podía hacerse con `Tag`:

```python
@admin.register(Activity)
class ActivityAdmin(FuzzySearchAdminMixin, ModelAdmin):
    list_per_page = 10000
    list_display = ("title", "description_truncated", "tag_list")
    search_fields = ("title",)
    autocomplete_fields = ("tags",)

    def get_search_haystack(self, obj):
        return [obj.title, obj.description, " ".join(t.title for t in obj.tags.all())]

    def tag_list(self, obj):
        return ", ".join(t.title for t in obj.tags.all()) or "-"

    tag_list.short_description = "Tags"
```

- Tanto `Tag` como `Activity` ahora tienen exactamente la misma búsqueda difusa (`FuzzySearchAdminMixin`) y son igual de "buscables" en el admin de `LocalPlace` (`get_search_haystack` de `LocalPlaceAdmin` incluye ambos: `tags` y `activities`).

**Status:** ⏳ Sigue pendiente de definición de negocio (¿son lo mismo? ¿se debería fusionar uno en el otro?). Documentado y técnicamente emparejados; falta la decisión de producto del cliente.

---

## 4 y 5. Renumeración de fotos / contador de fotos

No requirieron cambios — ya estaban resueltos:
- `LocalPlaceImageFormSet.clean()` valida `order` único por lugar.
- `LocalPlaceAdmin.image_count()` muestra la cantidad de imágenes en el listado.

**Status:** ✅ Ya resuelto (confirmado, sin cambios).

---

## 6. Reportes / filtros en Admin

**Antes:** solo `list_filter = ("category", "is_active")`, sin manera de ver "sin foto" o "3 estrellas", ni de exportar datos.

**Qué se hizo**, todo en `local_places/admin.py`:

### a) Filtro "¿Tiene fotos?" (ejemplo del cliente: "View all entries without a photograph")

```python
class HasPhotosFilter(admin.SimpleListFilter):
    title = "Has Photos"
    parameter_name = "has_photos"

    def lookups(self, request, model_admin):
        return (("yes", "With photos"), ("no", "Without photos"))

    def queryset(self, request, queryset):
        queryset = queryset.annotate(_image_count=Count("images"))
        if self.value() == "yes":
            return queryset.filter(_image_count__gt=0)
        if self.value() == "no":
            return queryset.filter(_image_count=0)
        return queryset
```

### b) Filtro por estrellas (ejemplo del cliente: "View all entries with 3-star recommendations")

```python
class PopularityStarsFilter(admin.SimpleListFilter):
    title = "Popularity (stars)"
    parameter_name = "stars"

    def lookups(self, request, model_admin):
        return (
            ("5", "5 stars"),
            ("4", "4 stars"),
            ("3", "3 stars"),
            ("2", "2 stars"),
            ("1", "1 star"),
            ("0", "Unrated / 0 stars"),
        )

    def queryset(self, request, queryset):
        value = self.value()
        if value is None:
            return queryset
        try:
            stars = Decimal(value)
        except InvalidOperation:
            return queryset
        if stars == 0:
            return queryset.filter(Q(popularity_score=0) | Q(popularity_score__isnull=True))
        # Bucket by whole star: e.g. "3" matches 3.0 - 3.9
        return queryset.filter(popularity_score__gte=stars, popularity_score__lt=stars + 1)
```

Ambos se agregaron a `list_filter`:

```python
list_filter = ("category", "is_active", HasPhotosFilter, PopularityStarsFilter)
```

### c) Exportar listado completo (ejemplo del cliente: "View all restaurants with all entered details")

Se activó `django-import-export`, que ya estaba en `requirements.txt` y comentado en el código (`# from import_export.admin import ImportExportModelAdmin`) pero nunca conectado:

```python
class LocalPlaceResource(resources.ModelResource):
    category = resources.Field(attribute="category__title", column_name="category")

    class Meta:
        model = LocalPlace
        fields = (
            "id", "name", "category", "description", "address", "contact_number",
            "website_url", "google_places_id", "google_places_link",
            "popularity_score", "review_count", "is_active", "created_at",
        )
        export_order = fields


@admin.register(LocalPlace)
class LocalPlaceAdmin(FuzzySearchAdminMixin, ExportMixin, ModelAdmin):
    resource_classes = [LocalPlaceResource]
    ...
```

Esto agrega un botón **"Export"** en el listado que respeta los filtros/búsqueda activos (categoría = Restaurants + Export → CSV/XLSX con todos los campos).

**Cómo cubre los 3 ejemplos del cliente:**
1. *"Restaurants con todos los detalles"* → filtrar por categoría "Restaurants" + botón Export.
2. *"Sin foto"* → filtro "Has Photos" = "Without photos".
3. *"3 estrellas"* → filtro "Popularity (stars)" = "3 stars".

**Status:** ✅ Implementado (antes: "Not feasible on current implementation" — sí era viable, solo faltaba conectar piezas que ya estaban en el proyecto).

---

## 7. Links clickeables en descripciones (Rich Text)

**Antes:** `LocalPlace.description`, `CartMap.description` y `Rule.description` eran `models.TextField()` planos — sin HTML, sin links.

**Qué se hizo** — se migraron los 3 campos a `CKEditor5Field` (el mismo editor que ya usa `legal.LegalDocument.content`, reutilizando la config `"extends"` ya definida en `settings.py`):

`local_places/models.py`:
```python
from django_ckeditor_5.fields import CKEditor5Field
...
class CartMap(models.Model):
    ...
    description = CKEditor5Field("Description", config_name="extends")   # antes: models.TextField()
...
class LocalPlace(models.Model):
    name = models.CharField(max_length=255)
    description = CKEditor5Field("Description", config_name="extends")   # antes: models.TextField()
```

`rules/models.py`:
```python
from django_ckeditor_5.fields import CKEditor5Field
...
class Rule(models.Model):
    ...
    title = models.CharField(max_length=255)
    description = CKEditor5Field("Description", config_name="extends")   # antes: models.TextField()
```

Se generaron y aplicaron las migraciones correspondientes:
- `local_places/migrations/0028_category_is_active_alter_cartmap_description_and_more.py`
- `rules/migrations/0004_alter_rule_description.py`

**Efecto colateral manejado:** como el campo ahora guarda HTML, las columnas `description_truncated` de los listados (`CartMapAdmin`, `RuleAdmin`) se actualizaron para usar `strip_tags()` antes de recortar el texto, así el listado no muestra etiquetas HTML crudas:

```python
def description_truncated(self, obj):
    plain = strip_tags(obj.description)
    return plain[:100] + "..." if plain and len(plain) > 100 else plain
```

**Cubre exactamente los ejemplos del cliente:** cart rentals y mapas → `CartMap.description`; reglas de playa/bicicletas → `Rule.description`; descripciones generales de lugares → `LocalPlace.description`.

**Status:** ✅ Implementado (antes: "Additional backend effort" — el esfuerzo fue mínimo porque el patrón ya existía en el proyecto para `legal`).

**Nota:** `Category`, `Activity` y `LiveLikeALocal` mantienen su descripción en texto plano (no mencionados en los ejemplos del cliente); se pueden convertir con el mismo patrón si hace falta.

---

## 8. Categorías/Reglas inactivas seguían mostrándose al usuario

**Diagnóstico real (no era solo un tema de frontend):** revisando las queries que expone la API, `RuleViewSet.queryset = Rule.objects.all()` no filtraba `is_active` de la regla ni de su categoría. `LocalPlace.category` (el modelo `Category` de Local Places) ni siquiera tenía un campo `is_active` — no existía forma de apagar una categoría de lugares desde el backend.

**Qué se hizo:**

### a) Se agregó `is_active` a `Category` (Local Places) — antes no existía

`local_places/models.py`:
```python
class Category(models.Model):
    title = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(
        default=True,
        help_text="Inactive categories, and the places under them, are hidden from the app.",
    )
```

`local_places/admin.py` — se expone en el listado y como filtro:
```python
@admin.register(Category)
class CategoryAdmin(FuzzySearchAdminMixin, ModelAdmin):
    list_per_page = 10000
    list_display = ("title", "description_truncated", "is_active")
    list_filter = ("is_active",)
```

### b) Se corrigieron los querysets de la API para excluir inactivos en cascada

`rules/views.py`:
```python
class RuleViewSet(viewsets.ReadOnlyModelViewSet):
    # Hide rules that were turned off directly, and rules whose parent
    # category was turned off — previously this returned everything and
    # relied entirely on the frontend to filter, so a rule/category toggled
    # off in Admin kept showing up in the API response.
    queryset = Rule.objects.filter(is_active=True, category__is_active=True)   # antes: Rule.objects.all()
```

`local_places/views.py`:
```python
from django.db.models import Q
...
class LocalPlaceViewSet(viewsets.ReadOnlyModelViewSet):
    # A place is hidden if it's inactive itself, OR if its category was
    # turned off in Admin (places without a category are unaffected).
    queryset = LocalPlace.objects.filter(is_active=True).filter(
        Q(category__isnull=True) | Q(category__is_active=True)
    )   # antes: LocalPlace.objects.filter(is_active=True)

class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Category.objects.filter(is_active=True)   # antes: Category.objects.all()

class RestaurantListView(generics.ListAPIView):
    ...
    def get_queryset(self):
        return LocalPlace.objects.filter(is_active=True).filter(
            Q(category__isnull=True) | Q(category__is_active=True)
        )   # antes: solo filtraba is_active del lugar
```

**Verificación funcional (corrida en shell de Django contra la base real):**
```
Rule visible despite inactive category? False (should be False)   ✔
Rule visible with active category?      True                       ✔
Place visible despite inactive category? False (should be False)  ✔
```

**Conclusión importante para el cliente:** contrario a lo que indicó Param, el problema **sí tenía una causa real en el backend** — la API nunca dio al frontend una señal confiable para filtrar, así que cualquier inconsistencia en el filtrado del FE se colaba directo. Ahora el backend es la fuente de verdad: aunque el frontend no filtre nada, un rule/categoría desactivada ya no aparece en la respuesta de la API.

**Status:** ✅ Implementado en backend (antes: "Pending / In progress on FE"). Si el FE tenía lógica propia de filtrado duplicada, ahora es redundante pero inofensiva — se puede simplificar/quitar del lado del cliente si se desea.

---

## Resumen de estados

| # | Issue | Estado anterior | Estado ahora |
|---|---|---|---|
| 1 | Búsqueda en Admin | Pending | ✅ Implementado (búsqueda difusa en todos los listados + dropdown en Local Places) |
| 2 | Quitar paginación | Resolved | ✅ Ya resuelto (sin cambios) |
| 3 | Tags vs Activities | Needs clarification | ⏳ Paridad técnica aplicada; decisión de producto sigue pendiente |
| 4 | Renumeración de fotos | Resolved | ✅ Ya resuelto (sin cambios) |
| 5 | Contador de fotos | Resolved | ✅ Ya resuelto (sin cambios) |
| 6 | Reportes/filtros | Not feasible | ✅ Implementado (2 filtros nuevos + export CSV/XLSX) |
| 7 | Links clickeables en descripciones | Additional effort | ✅ Implementado (CKEditor5 en 3 modelos) |
| 8 | Categoría/Regla inactiva visible | In progress on FE | ✅ Implementado en backend (bug real corregido) |

## Cómo probar

```bash
cd tybee-be
source venv/bin/activate
python manage.py migrate
python manage.py runserver 0.0.0.0:8001
```

- Admin: `http://127.0.0.1:8001/admin/local_places/localplace/` — probar buscar con errores de tipeo, usar los filtros "Has Photos" / "Popularity (stars)", exportar, y ver la descripción con el editor rich text.
- API: `GET /rules/` y `GET /local/places/` con un usuario autenticado — desactivar una `RuleCategory` o `Category` desde el admin y confirmar que sus items dejan de aparecer.
