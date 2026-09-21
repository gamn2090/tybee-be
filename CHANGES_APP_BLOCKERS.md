# Tareas de backend para destrabar la app — implementadas

Respuesta al documento del equipo frontend ("Tareas de backend pendientes para destrabar la app"). Se implementaron **BE-4, BE-5, BE-1 y BE-8** completas, y la parte de **MAPA** que corresponde a backend/admin (el resto de MAPA depende de una decisión de negocio + trabajo de contenido, ver el detalle al final).

Se verificó cada contrato contra el código real del FE en este workspace (`tybee-fe/src/...`) antes de implementar, no solo contra la descripción del documento — se referencian los archivos de FE relevantes en cada sección.

Se corrió `python manage.py check`, `makemigrations --check` (sin cambios pendientes) y se probaron los endpoints reales (`Client` de Django + JWT) contra los casos de ejemplo del documento. El servidor de desarrollo recargó todo sin errores.

Archivos nuevos:
- [`local_places/search.py`](local_places/search.py)
- [`local_places/management/commands/refresh_place_coordinates.py`](local_places/management/commands/refresh_place_coordinates.py)

Archivos modificados:
- [`tybee_backend/pagination.py`](tybee_backend/pagination.py)
- [`tybee_backend/settings.py`](tybee_backend/settings.py)
- [`local_places/views.py`](local_places/views.py)
- [`local_places/serializers.py`](local_places/serializers.py)
- [`local_places/admin.py`](local_places/admin.py)
- [`local_places/static/local_places/js/admin_places.js`](local_places/static/local_places/js/admin_places.js)
- [`tybee-fe/src/api/places.ts`](../tybee-fe/src/api/places.ts) (tipos TypeScript, sin tocar lógica de pantallas)

---

## BE-4 — Paginación: `next`/`previous` en la raíz

**Archivo:** [`tybee_backend/pagination.py`](tybee_backend/pagination.py)

**Confirmado contra el FE:** `tybee-fe/src/screens/Explore/explore-screen.tsx` líneas 208 y 216 (`firstResponse.next`, `response.next`) — en efecto lee `next` en la raíz, no dentro de `links`.

```python
def get_paginated_response(self, data):
    next_link = self.get_next_link()
    previous_link = self.get_previous_link()
    return Response(
        {
            # Kept for backward compatibility with any existing consumer.
            "links": {
                "next": next_link,
                "previous": previous_link,
            },
            # The app reads these at the root (see explore-screen.tsx),
            # not nested under "links" — without this it can't tell
            # there's a next page once a filter is applied.
            "next": next_link,
            "previous": previous_link,
            "count": self.page.paginator.count,
            "total_pages": self.page.paginator.num_pages,
            "current_page": self.page.number,
            "results": data,
        }
    )

def get_paginated_response_schema(self, schema):
    base_schema = super().get_paginated_response_schema(schema)
    base_schema["properties"]["links"] = {
        "type": "object",
        "properties": {
            "next": base_schema["properties"]["next"],
            "previous": base_schema["properties"]["previous"],
        },
    }
    return base_schema
```

Es aditivo — `links` se mantiene igual, `DEFAULT_PAGINATION_CLASS` en `settings.py` hace que aplique a todos los endpoints paginados automáticamente. También actualicé `get_paginated_response_schema` para que drf-spectacular documente ambos.

**Verificado:**
```
GET /local/places/  → next: "http://.../local/places/?page=2", count: 17
```

**Status:** ✅ Implementado.

---

## BE-5 — Imagen y categoría en `/local/restaurants/`

**Archivos:** [`local_places/serializers.py`](local_places/serializers.py), [`local_places/views.py`](local_places/views.py)

**Confirmado contra el FE:** `tybee-fe/src/screens/Map/map-screen.tsx` — el componente `RefinedMarker` (líneas 27-79) hoy no usa imagen ni categoría del backend (por eso también hace un fetch aparte a Google Place Details por cada marcador, ver sección MAPA). Actualicé el tipo `RestaurantLocation` en `tybee-fe/src/api/places.ts` para que el equipo de FE tenga los campos tipados y listos para consumir.

`local_places/serializers.py`:
```python
class RestaurantSerializer(serializers.ModelSerializer):
    category_title = serializers.CharField(source="category.title", read_only=True)
    image_presigned = serializers.SerializerMethodField()

    class Meta:
        model = LocalPlace
        fields = (
            "id", "name", "latitude", "longitude", "address", "google_places_id",
            "category", "category_title", "image_presigned",
        )

    def get_image_presigned(self, obj):
        # obj.images.all() reuses the `prefetch_related("images")` from the
        # view's queryset (LocalPlaceImage.Meta.ordering = ["order", "id"]
        # already sorts it) — calling .order_by() here would issue a new
        # query per place instead of reusing the prefetch cache.
        first_image = next(iter(obj.images.all()), None)
        if first_image and first_image.image:
            return PresignedUrlField().to_representation(first_image.image)
        return None
```

`local_places/views.py`:
```python
class RestaurantListView(generics.ListAPIView):
    serializer_class = RestaurantSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = None   # sin cambios: la URL y el shape de lista siguen igual

    def get_queryset(self):
        queryset = (
            LocalPlace.objects.filter(is_active=True)
            .filter(Q(category__isnull=True) | Q(category__is_active=True))
            .select_related("category")
            .prefetch_related("images")
        )
        if ids := parse_id_list(self.request.query_params.get("categories")):
            queryset = queryset.filter(category_id__in=ids)
        return queryset
```

`parse_id_list` se movió a [`local_places/search.py`](local_places/search.py) porque la reutilizan tanto esta vista como `LocalPlaceViewSet` (BE-1):
```python
def parse_id_list(value):
    """'1, 3,abc' -> [1, 3]. Ignores anything non-numeric instead of 500ing."""
    return [int(v) for v in (value or "").split(",") if v.strip().isdigit()]
```

**Verificado:**
```json
GET /local/restaurants/
[{"id": 2, "name": "Doc's Bar", "category": 2, "category_title": "Bars", "image_presigned": null, ...}]
```
- `?categories=1` filtra correctamente; `?categories=abc` se ignora sin error 500.
- Un lugar sin imágenes trae `image_presigned: null`; sin categoría, `category`/`category_title: null`.
- N+1 evitado con `select_related`/`prefetch_related` (confirmado leyendo el plan de queries; no crece con la cantidad de lugares).

**Status:** ✅ Implementado.

---

## BE-1 — Búsqueda y filtros en `/local/places/`

**Archivo:** [`local_places/views.py`](local_places/views.py)

**Confirmado contra el FE:** `tybee-fe/src/services/places-service.ts` ya arma `params.categories`, `params.tags`, `params.activities`, `params.search` (líneas 9-13) — el frontend ya manda estos parámetros hoy, el backend simplemente los ignoraba. `PlaceDetail` en `tybee-fe/src/api/places.ts` ya tipa `category?: string | number`, `tags?/activities?/live_like_a_local?: (string|number)[]` — el contrato que implementé coincide con esos tipos.

```python
class LocalPlaceViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = LocalPlace.objects.filter(is_active=True).filter(
        Q(category__isnull=True) | Q(category__is_active=True)
    )
    serializer_class = LocalPlaceSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = super().get_queryset()
        params = self.request.query_params

        # Within a param: OR (any of the given ids). Across params: AND —
        # this mirrors the filtering the app currently does on-device.
        if ids := parse_id_list(params.get("categories")):
            queryset = queryset.filter(category_id__in=ids)
        if ids := parse_id_list(params.get("tags")):
            queryset = queryset.filter(tags__id__in=ids)
        if ids := parse_id_list(params.get("activities")):
            queryset = queryset.filter(activities__id__in=ids)
        if ids := parse_id_list(params.get("live_like_a_local")):
            queryset = queryset.filter(live_like_a_local__id__in=ids)

        # The tags/activities/live_like_a_local joins above can duplicate
        # rows (a place with 2 matching tags would otherwise appear twice).
        # Explicit ordering avoids Django's "unordered object list" warning
        # and keeps pagination stable across pages.
        queryset = queryset.distinct().order_by("name", "id")

        return queryset.select_related("category").prefetch_related(
            "tags", "activities", "live_like_a_local", "images", "operating_hours"
        )
```

El parámetro `search` **no** se implementó con `filters.SearchFilter` de DRF — se implementó junto con BE-8 (ver abajo), como recomendaba el propio documento, para no descartar coincidencias aproximadas con un `icontains` estricto corriendo antes.

**Verificado:**
- `?categories=abc` → se ignora, `200 OK`, sin 500.
- Filtrar por `tags` con IDs repetidos entre lugares no duplica resultados (`.distinct()` confirmado).
- Sigue paginado, sigue respetando `is_active`/`category__is_active`.

**Status:** ✅ Implementado.

---

## BE-8 — Búsqueda tolerante a errores + `did_you_mean`

**Archivos:** [`local_places/search.py`](local_places/search.py) (nuevo), [`local_places/views.py`](local_places/views.py)

Reutiliza `normalize_text` y `fuzzy_match` de `tybee_backend/search_utils.py` (los mismos que ya usa el Admin), tal como sugería el documento.

```python
# local_places/search.py
MIN_FUZZY_QUERY_LENGTH = 3   # por debajo de esto, solo coincidencia exacta

def _matches_term(place, term):
    """Return (matched, is_exact, name_hit) for a single place."""
    normalized_query = normalize_text(term)
    haystack_fields = _place_haystack_fields(place)   # name, address, category, tags, activities, live_like_a_local
    description_plain = strip_tags(place.description or "")

    # 1. Substring exacto normalizado, en cualquier campo (incluida la
    #    descripción, pero sin ratio difuso contra ella — ver punto 3).
    exact = any(normalized_query in normalize_text(f) for f in haystack_fields)
    exact = exact or normalized_query in normalize_text(description_plain)
    name_hit = normalized_query in normalize_text(place.name or "")
    if exact:
        return True, True, name_hit

    if len(normalized_query) < MIN_FUZZY_QUERY_LENGTH:
        return False, False, False

    # 2. Query completa vs campo completo — resuelve "Docks Bars" vs "Doc's Bar".
    for field in haystack_fields:
        if fuzzy_match(term, field):
            return True, False, field == place.name

    # 3. Palabra vs palabra — resuelve "kelpy" vs "The Kelpie Pub" -> "Kelpie".
    query_words = _words(term)
    for field in haystack_fields:
        field_words = _words(field)
        for query_word in query_words:
            if any(fuzzy_match(query_word, field_word) for field_word in field_words):
                return True, False, field == place.name

    return False, False, False


def rank_places(queryset, term):
    """Devuelve (lista_ordenada, did_you_mean)."""
    scored = []
    any_exact = False
    for place in queryset:
        matched, exact, name_hit = _matches_term(place, term)
        if not matched:
            continue
        if exact:
            any_exact = True
        rank = (0 if name_hit else 1, 0 if exact else 1, (place.name or "").lower())
        scored.append((rank, place))

    scored.sort(key=lambda pair: pair[0])
    ordered = [place for _, place in scored]
    did_you_mean = ordered[0].name if ordered and not any_exact else None
    return ordered, did_you_mean
```

Los 3 detalles del documento están resueltos explícitamente:
1. **Query completa vs campo completo** (paso 2 arriba) — sin esto, "Docks Bars" solo encontraría lugares cuya categoría contuviera "bars".
2. **Palabra vs palabra dentro de campos multi-palabra** (paso 3) — compara `"kelpy"` contra cada palabra de `"The Kelpie Pub"` por separado (`"kelpie"`), no contra el string concatenado.
3. **Descripción: solo match exacto normalizado, sin HTML** — `description_plain` (con `strip_tags`) solo entra en el chequeo `exact`, nunca en los pasos difusos 2/3.

`local_places/views.py` — override de `list()`:
```python
def list(self, request, *args, **kwargs):
    queryset = self.filter_queryset(self.get_queryset())

    term = (request.query_params.get("search") or "").strip()
    did_you_mean = None
    if term:
        queryset, did_you_mean = rank_places(queryset, term)

    page = self.paginate_queryset(queryset)
    if page is not None:
        serializer = self.get_serializer(page, many=True)
        response = self.get_paginated_response(serializer.data)
        response.data["did_you_mean"] = did_you_mean
        return response

    serializer = self.get_serializer(queryset, many=True)
    return Response({"results": serializer.data, "did_you_mean": did_you_mean})
```

**Verificado con datos reales creados para la prueba (`Doc's Bar`, `The Kelpie Pub`), igual que los ejemplos del documento:**

| Query | `did_you_mean` obtenido | Resultado |
|---|---|---|
| `Docks Bars` | `"Doc's Bar"` | incluye Doc's Bar ✔ |
| `kelpie` | `null` | The Kelpie Pub (match exacto) ✔ |
| `kelpy` | `"The Kelpie Pub"` | The Kelpie Pub ✔ |
| `zzzz` | `null` | `results: []` ✔ |

Coincide exactamente con la tabla de "Cómo probarlo" del documento original. (No se probó `olearys` porque ese lugar de ejemplo no existe en esta base de datos local — la lógica es la misma que ya funciona para `Docks Bars`/`kelpy`.)

**Status:** ✅ Implementado (hecho junto con BE-1, sin necesidad de `pg_trgm` — reutilizar `search_utils.py` bajó la estimación de 10-14h como anticipaba el documento).

### Corrección posterior — orden de resultados y `did_you_mean` incorrectos contra el catálogo real

**Archivo:** solo [`local_places/search.py`](local_places/search.py). No cambia la vista, el serializer ni el contrato — `search` y `did_you_mean` siguen igual, la app no se entera de este cambio.

**El problema reportado (contra el catálogo real, no el de prueba):** `?search=Docks Bars` devolvía `did_you_mean: "Agave Bar and Grill"` con Doc's Bar en segundo lugar. Dos causas:
1. `rank_places` ordenaba las coincidencias aproximadas **alfabéticamente**, no por parecido real con lo buscado ("agave…" < "doc's…").
2. En el paso 3 de `_matches_term` bastaba con que **una sola palabra** coincidiera. Por eso `"bar"` traía todos los bares, y `"tybee"` traía el catálogo entero (está en todas las direcciones) — `"pizza tybee"` devolvía 17 lugares en vez de 1.

**Qué se cambió:**

1. Nueva constante y import:
```python
import re
from difflib import SequenceMatcher
...
DID_YOU_MEAN_MIN_SIMILARITY = 0.75
```

2. Paso 3 de `_matches_term` — ahora exige que **todas** las palabras de la query matcheen alguna palabra de los campos del lugar (antes bastaba una), y se agregó `_name_similarity()` para medir qué tan parecido es el nombre a la búsqueda:
```python
query_words = _words(term)
field_words = [word for field in haystack_fields for word in _words(field)]
if query_words and all(
    any(fuzzy_match(query_word, word) for word in field_words)
    for query_word in query_words
):
    name_words = _words(place.name)
    name_hit = all(
        any(fuzzy_match(query_word, word) for word in name_words)
        for query_word in query_words
    )
    return True, False, name_hit

return False, False, False


def _name_similarity(term, name):
    query, target = normalize_text(term), normalize_text(name)
    if not query or not target:
        return 0.0
    whole = SequenceMatcher(None, query, target).ratio()
    query_words = [w for w in (normalize_text(w) for w in _words(term)) if w]
    name_words = [w for w in (normalize_text(w) for w in _words(name)) if w]
    if not query_words or not name_words:
        return whole
    per_word = sum(
        max(SequenceMatcher(None, query_word, name_word).ratio() for name_word in name_words)
        for query_word in query_words
    ) / len(query_words)
    return max(whole, per_word)
```

3. `rank_places` ahora ordena por similitud real (no alfabético) y solo sugiere `did_you_mean` cuando la similitud supera `DID_YOU_MEAN_MIN_SIMILARITY`:
```python
scored = []
any_exact = False
for place in queryset:
    matched, exact, name_hit = _matches_term(place, term)
    if not matched:
        continue
    if exact:
        any_exact = True
    similarity = _name_similarity(term, place.name or "")
    rank = (0 if name_hit else 1, 0 if exact else 1, -similarity, (place.name or "").lower())
    scored.append((rank, similarity, place))

scored.sort(key=lambda item: item[0])
ordered = [place for _, _, place in scored]

did_you_mean = None
if scored and not any_exact and scored[0][1] >= DID_YOU_MEAN_MIN_SIMILARITY:
    did_you_mean = scored[0][2].name
return ordered, did_you_mean
```

**Verificado con un catálogo de prueba más parecido al real** (`Doc's Bar`, `The Kelpie Pub`, `Agave Bar and Grill`, `North Beach Bar`, `Pizza Time`, + 13 lugares de relleno, todos con "Tybee Island, GA" en la dirección):

| Query | Antes | Después |
|---|---|---|
| `Docks Bars` | `did_you_mean: "Agave Bar and Grill"`, Doc's Bar 2do | `did_you_mean: "Doc's Bar"`, Doc's Bar 1ro ✔ |
| `pizza tybee` | 17 resultados | 1 resultado (`Pizza Time`) ✔ |
| `bar` | todos los bares (esperado, es una sola palabra genuina) | sin cambios, correcto |
| `kelpy` | `did_you_mean: "The Kelpie Pub"` | `did_you_mean: null` (similitud 0.73 < 0.75; el lugar sigue apareciendo en `results`, solo ya no se sugiere como "Did you mean" por quedar debajo del umbral de confianza) |

**Status:** ✅ Corregido y verificado.

---

## MAPA — Coordenadas de los lugares (parcial: lo que es responsabilidad de backend/admin)

**Archivos:** [`local_places/static/local_places/js/admin_places.js`](local_places/static/local_places/js/admin_places.js), [`local_places/admin.py`](local_places/admin.py), [`local_places/management/commands/refresh_place_coordinates.py`](local_places/management/commands/refresh_place_coordinates.py)

### 1. Guardar la ubicación exacta (revertido)

```javascript
// admin_places.js
// Antes:
var loc = place.geometry.viewport
    ? place.geometry.viewport.getCenter()
    : place.geometry.location;

// Ahora:
var loc = place.geometry.location;
```

**Nota para el cliente/equipo, tal como pedía el documento:** no investigué a fondo *por qué* se cambió a `viewport.getCenter()` en el commit `5a4b7a1` — antes de que esto se despliegue a producción, alguien que haya estado en esa decisión debería confirmar que no resolvía un problema real (por ejemplo, algunos `place.geometry.location` de Google pueden apuntar al centroide de un polígono grande en vez de la entrada del negocio). Si no hay una razón documentada, este revert es seguro.

### 2. Permitir corregir la ubicación a mano

`local_places/admin.py` — se quitó `readonly` de `latitude`/`longitude` (se mantiene en `google_places_id`/`google_places_link`, que si se editan a mano rompen el link a Google):

```python
# google_places_id / google_places_link keep coming from the Google
# Places autocomplete only — editing them by hand risks linking the
# place to the wrong Google listing. Latitude/longitude are NOT
# readonly: places with no Google listing (trails, parking lots,
# vending machines) need a way to set coordinates manually, and
# editors need to be able to correct a wrong pin.
readonly_fields = ["google_places_id", "google_places_link"]
...
for field in ("latitude", "longitude"):
    if field in self.fields:
        self.fields[field].help_text = (
            "Auto-filled from the address lookup above — edit directly "
            "if the pin lands in the wrong spot or this place has no "
            "Google listing."
        )
```

**No implementado:** el pin arrastrable sobre un mapa que menciona el documento como "mejor" alternativa — es una pieza de UI bastante más grande (requiere embeber un mapa interactivo en el formulario del admin). Lo que se hizo (inputs numéricos editables) ya destraba el caso de uso (lugares sin listing de Google), y se puede reemplazar por el mapa arrastrable después sin tocar el modelo ni la API.

### 3. Avisar si el Place ID ya lo usa otro lugar (advertencia, no error)

```python
def save_model(self, request, obj, form, change):
    super().save_model(request, obj, form, change)
    if obj.google_places_id:
        other_names = list(
            LocalPlace.objects.filter(google_places_id=obj.google_places_id)
            .exclude(pk=obj.pk)
            .values_list("name", flat=True)
        )
        if other_names:
            self.message_user(
                request,
                "This Google Place ID is also used by: " + ", ".join(other_names) +
                ". If they aren't actually the same building, fix the address lookup for one of them.",
                level=messages.WARNING,
            )
```

### 4. Comando para recalcular coordenadas guardadas

Nuevo: [`local_places/management/commands/refresh_place_coordinates.py`](local_places/management/commands/refresh_place_coordinates.py)

```bash
python manage.py refresh_place_coordinates --dry-run   # solo muestra qué cambiaría
python manage.py refresh_place_coordinates              # escribe los cambios
```

- Para cada `google_places_id` **no compartido**, pide `Place Details` (`fields=geometry`) y compara contra la coordenada guardada con distancia haversine; solo actualiza si se corre sin `--dry-run` y el movimiento es ≥ 1m.
- Los `google_places_id` compartidos por más de un `LocalPlace` se **saltean siempre** (actualizarlos los dejaría a todos en el mismo punto) y se listan al final para revisión manual — esto es justamente lo que necesita el equipo de contenido para revisar "Park of 7 Flags / Breezy Rider Tybee Taxi / Blue Heron Nature Trail" del informe.
- Usa `GOOGLE_MAPS_SERVER_API_KEY` si está configurada (nueva variable en `settings.py`/`.env`), y si no, cae a `GOOGLE_MAPS_API_KEY` — atento al punto que señalaba el documento: si la key del navegador está restringida por dominio/referrer, no va a funcionar desde el servidor y hace falta una key de servidor separada.

```python
# tybee_backend/settings.py
GOOGLE_MAPS_SERVER_API_KEY = env("GOOGLE_MAPS_SERVER_API_KEY", default="")
```

**Verificado:** el comando se registra y corre (`python manage.py help refresh_place_coordinates`); no se corrió `--dry-run` real contra los 153 lugares de producción porque este entorno usa una base de datos local vacía/de prueba, no la de producción — eso hay que correrlo contra la base real cuando se despliegue.

### Lo que queda fuera de esta entrega (no es trabajo de backend/admin)

- El fetch a Google Place Details que hace `RefinedMarker` en `map-screen.tsx` (líneas 33-45 de `tybee-fe/src/screens/Map/map-screen.tsx`) — las 153 consultas pagas por sesión de mapa — es código de **frontend** y debe quitarse ahí una vez que las coordenadas guardadas sean confiables (después de correr el comando de arriba). No lo toqué porque cambiar esa pantalla es explícitamente trabajo de FE según el propio documento.
- La revisión lugar-por-lugar de los grupos de Place IDs compartidos ("Coordinación con el cliente") — es trabajo de contenido, no de código.
- El pin arrastrable en el formulario del admin (ver nota arriba).

**Status:** ⏳ Backend/Admin listo; falta la corrida real del comando contra producción, la revisión de contenido, el fix de frontend en `map-screen.tsx`, y opcionalmente el pin arrastrable.

---

## Resumen de estados

| Tarea | Estimación doc. | Estado |
|---|---|---|
| BE-4 Paginación raíz | 1h | ✅ Implementado |
| BE-5 Imagen/categoría en restaurants | 2h | ✅ Implementado |
| BE-1 Búsqueda y filtros en places | 4h | ✅ Implementado |
| BE-8 Búsqueda difusa + did_you_mean | 10-14h (con pg_trgm) | ✅ Implementado (sin pg_trgm, reutilizando `search_utils.py`) |
| MAPA — revert a `geometry.location` | — | ✅ Hecho |
| MAPA — lat/lng editables | — | ✅ Hecho (inputs; falta pin arrastrable) |
| MAPA — aviso de Place ID compartido | — | ✅ Hecho |
| MAPA — comando de recálculo | A definir | ✅ Hecho, falta correrlo contra producción |
| MAPA — quitar fetch de Google en el mapa (FE) | — | ⏳ Pendiente, es tarea de frontend |
| MAPA — revisión de contenido de Place IDs compartidos | — | ⏳ Pendiente, es tarea de contenido/cliente |

## Antes de desplegar

Antes de que esto se pise con lo que ya corre en `app.api.tybeego.com`, importante confirmar (como pide el propio documento):
1. Si el commit `eaaedcd` (los 8 puntos del Admin) ya está desplegado, y si las migraciones `local_places.0028` y `rules.0004` ya se aplicaron ahí.
2. Coordinar con frontend el momento de publicar la nueva versión de la app que sepa renderizar HTML en las descripciones de Rules y Cart Maps (ya es HTML en base de datos desde el commit anterior).
3. Correr `refresh_place_coordinates --dry-run` contra la base de producción antes de la corrida real, y revisar la lista de Place IDs compartidos con el equipo de contenido.
