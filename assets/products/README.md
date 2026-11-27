# Fotos de producto aportadas por el operador

Coloca aquí las imágenes reales que quieres que use el motor. **No se descargan ni se extraen de Amazon**: las aportas tú y confirmas que tienes derecho a usarlas.

## Nombres admitidos

- `assets/products/<ASIN>.jpg`
- `assets/products/<ASIN>.jpeg`
- `assets/products/<ASIN>.png`
- `assets/products/<ASIN>.webp`
- `assets/products/<slug>.<ext>` (el slug de la página, por ejemplo `wolfbox-mv24a-jump-starter.jpg`)

Opcionalmente puedes aportar una segunda foto para la variante 2:

- `assets/products/<ASIN>-2.jpg`
- `assets/products/<slug>-2.jpg`

## Uso

Tras copiar las imágenes, ejecuta:

```powershell
python scripts/build_media_from_photos.py
```

El script reemplaza los `image-*.png` y `clip-*.mp4` correspondientes en `docs/media/<slug>/`, mantiene el CTA y el disclosure exactos, y actualiza `data/content_assets.json`. Si un ASIN no tiene foto, conserva su concept visual actual.

Regla de compliance: no se añaden precios ni especificaciones inventadas. Las imágenes se marcan como `Photo supplied by operator` en el propio archivo.
