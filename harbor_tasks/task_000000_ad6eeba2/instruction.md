Migrating our asset inventory from the old system and ran into a wall. Exported everything to /home/user/inventory/assets.csv but the importer on the new system only speaks JSON and it's picky — needs the data normalized a specific way. The old system had some... creative data entry over the years.

The CSV has asset records with purchase dates in at least three different formats (MM/DD/YYYY, YYYY-MM-DD, and some European DD.MM.YYYY mixed in), prices that sometimes have dollar signs and commas, some fields quoted inconsistently, and a handful of rows where someone put the serial number in the wrong column. Also pretty sure there are duplicate asset IDs that need to be deduplicated — keep the one with the latest purchase date when that happens.

Need a clean /home/user/inventory/assets.json that the new system can actually ingest. Should be an array of objects with id, name, serial, purchase_date (ISO 8601), price_cents (integer), and location. Any row that's too mangled to parse should go to /home/user/inventory/rejected.json with the original row and a reason field.

The importer validates pretty strictly — if purchase_date isn't valid ISO 8601 or price_cents isn't a positive integer, it'll choke on the whole file.
