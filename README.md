# Shawarma Street

Django restaurant site with a responsive menu, food gallery, restaurant story,
contact links, mobile navigation, and scroll animations. The existing food photos,
red/cream/black palette, and typography are kept in local restaurant assets.

## Local development

Use Python 3.12 or newer. In PowerShell:

```powershell
python -m pip install -r requirements.txt
$env:DJANGO_DEBUG = "true"
python manage.py migrate
python manage.py runserver
```

Environment variables must be set in your shell or hosting provider; `.env.example`
documents the supported values and is not loaded automatically.

## Structure

- `shawarma_street/`: settings, root routing, WSGI and ASGI entry points.
- `restaurant/`: menu models, migrations, admin management, homepage view, and tests.
- `restaurant/templates/restaurant/restaurant.html`: restaurant page layout.
- `restaurant/templates/restaurant/menu.html`: database-backed menu rendering.
- `restaurant/static/restaurant/`: stylesheet, interactions, and three image assets.
- `db.sqlite3`: menu, staff accounts and sessions; excluded from version control.
- `media/menu/`: uploaded category and dish photos; excluded from version control.
- `collected_static/`: generated deployment assets; excluded from version control.

## Verification

```powershell
python manage.py check
python manage.py test
python manage.py collectstatic --noinput
```

## Deployment

Set `DJANGO_DEBUG=false`, a unique random `DJANGO_SECRET_KEY`, and
`DJANGO_ALLOWED_HOSTS` to the exact hostnames, separated by commas. Set
`DJANGO_CSRF_TRUSTED_ORIGINS` to HTTPS origins when required by your deployment.
Run migrations and collectstatic during deployment. Serve
`shawarma_street.wsgi:application` or `shawarma_street.asgi:application` with your
host's production server; Django's development server is for local use only.
HTTPS redirects, secure cookies, and HSTS are enabled in production. Only the
Vercel environment enables forwarded HTTPS headers; other trusted reverse proxies
must be configured explicitly.

### Vercel

Vercel detects `manage.py`, the WSGI entry point, and static-file configuration
automatically; no `vercel.json` build override is needed. Before the first
production deployment, add these **Production** environment variables in the
Vercel project settings:

```text
DJANGO_DEBUG=false
DJANGO_SECRET_KEY=<a newly generated, private Django secret>
DATABASE_URL=postgresql://USER:PASSWORD@HOST:PORT/DATABASE
DJANGO_ALLOWED_HOSTS=<project>.vercel.app,<your-custom-domain>
DJANGO_CSRF_TRUSTED_ORIGINS=https://<project>.vercel.app,https://<your-custom-domain>
```

`DATABASE_URL` is deliberately mandatory on Vercel: SQLite and uploaded files
are not persistent there. Create a hosted PostgreSQL database first, then run
`python manage.py migrate` once against that database before directing visitors
to the deployment. Do not put production database credentials in `.env`,
`vercel.json`, or Git. Give preview deployments an isolated database and their
own environment variables; otherwise leave them unconfigured so they fail safely
instead of sharing production data.

For generated Vercel URLs, `.vercel.app` and `https://*.vercel.app` are accepted
automatically. Explicit environment values remain necessary for custom domains.

In development, Django serves uploaded files at `/media/` when `DJANGO_DEBUG=true`.
In production, configure the web server or a media storage service to serve that
URL from persistent media storage, without executing uploaded files. WhiteNoise
and `collectstatic` serve static assets only; they do not publish media uploads.
Back up the selected database and media directory together. Local media support is
unchanged; PostgreSQL stores image references, not uploaded image files. Uploaded
media persistence on Vercel remains a separate deployment task; Cloudinary and
custom domain configuration are intentionally deferred.

## Manage the menu

### Customise the admin appearance

The editable admin HTML shell is
`restaurant/admin_portal/templates/admin/base_site.html`. It extends Django's
admin base so navigation, login, forms, permissions, filters, and theme switching
continue to work. Edit its `branding` block to change the header HTML; add inherited
template blocks here for further layout customisation. Admin titles and menu
configuration remain in `restaurant/admin.py`.

Colours and spacing live in
`restaurant/static/restaurant/admin/restaurant-admin.css`. Defaults retain the
current Django appearance. Edit the header colour variables, light/dark palette
blocks, content/header padding, form padding, table padding, and module gap.
Tablet/mobile spacing is defined in the media queries at the bottom. Login and
popup spacing remains Django's default. Automatic colour mode follows Django's
system palette; the explicit light/dark blocks apply to the theme toggle selections.

Refresh the browser after editing; use a hard refresh if CSS is cached. On deployment,
run `python manage.py collectstatic --noinput` to publish stylesheet changes.
The template directory is prioritised in `shawarma_street/settings.py`; no separate
admin app or database migration is required.

Log in at `http://127.0.0.1:8000/admin/`. Under **Shawarma Street**, use **Menu
categories** and **Menu items**:

1. Add a category with a name and unique slug. Description and photo are optional.
2. Add a dish, choose its category, upload a photo, and enter its description and MRP.
3. Optionally set a discount below MRP, or a badge such as **Most loved**.
4. Edit **display order** in either list to reorder the public menu; lower numbers
   appear first, with name and ID breaking ties.
5. Toggle **Available to order** in the item list and click **Save**. Unavailable
   dishes remain visible with their order links disabled. Clear **Show category
   on menu** to hide a category and all its dishes.

Saving updates the public page on its next refresh. No build or synchronization is
needed. Prices retain the existing dollar currency. MRP must be positive; a discount
must be positive and strictly below MRP. Uploads accept verified JPEG, PNG and WebP
images up to 5 MB and 20 megapixels. Slugs must be unique within each model.
Categories containing dishes are protected from deletion; move or delete dishes first.

For non-superuser staff, an administrator can create a **Menu managers** group under
**Authentication and Authorization → Groups** and grant view/add/change/delete
permissions for **Menu category** and **Menu item** as appropriate. Assign users to
the group and enable their **Active** and **Staff status** flags. No superuser flag
or user-management permissions are needed to manage the menu.

`python manage.py migrate` applies `0001_initial` and `0002_seed_restaurant_menu`.
The seed preserves Chicken, Beef and Mixed Shawarma, their prices, and the Most loved
badge, copying the existing photograph to `media/menu/items/`. It runs once and does
not overwrite staff edits. Both migrations have already been applied locally.
Image replacements and deletions do not automatically delete old files; keep backups
and remove unreferenced media separately when appropriate.

Order buttons lead to the menu; available dish links and Locations open an email enquiry.
Catering and Franchise also use the existing contact email. There is no checkout,
payment collection, or confirmed branch directory. Replace the contact details with
verified business information before launch. The three social links deliberately
retain their `#` placeholders for the owner to supply later.


## Production Database Setup

LOCAL: SQLite ? `db.sqlite3` in the project directory when `DATABASE_URL` is absent.
The existing optional `RESTAURANT_DATABASE_PATH` override is preserved.
PRODUCTION: PostgreSQL ? `DATABASE_URL`, which takes precedence over the SQLite path.
An empty, malformed, incomplete or non-PostgreSQL URL raises a configuration error;
connection/authentication failures never trigger a SQLite fallback. Keep the variable
unset locally (do not set it to an empty string). Vercel must have it configured.

The URL parser is `dj-database-url`; `psycopg[binary]` supplies the PostgreSQL driver
without requiring a compiler or system libpq. Django connections close after each
request (`CONN_MAX_AGE=0`); server-side cursors are disabled for transaction poolers.
Use your provider's URL with its required TLS options (such as `sslmode=require`,
or `verify-full` with the provider's certificate configuration). URL-encode special
characters in credentials. Never paste credentials into source, `vercel.json`, logs,
or committed fixtures. `.env` and `.env.*` are ignored except `.env.example`, which
contains placeholders only; environment files are not automatically loaded.

### Future deployment procedure (not performed)

1. Create a hosted PostgreSQL database supported by Django 6 (PostgreSQL 14+).
2. Obtain its connection URL and required TLS settings. Use the provider's pooling
   endpoint for serverless traffic if recommended, and its direct endpoint for
   migrations if required by the provider.
3. In Vercel Project Settings ? Environment Variables, add `DATABASE_URL` for
   Production. Use a separate database for Preview deployments. Also configure
   `DJANGO_DEBUG=false`, a private `DJANGO_SECRET_KEY`, exact
   `DJANGO_ALLOWED_HOSTS`, and HTTPS `DJANGO_CSRF_TRUSTED_ORIGINS` as needed.
4. Redeploy with the existing `vercel.json` build command. Keep traffic off the new
   deployment until migrations and setup are complete.
5. From a trusted local shell or one-off CI job with this checkout, dependencies,
   and the production environment supplied securely, run:
   ```powershell
   python manage.py migrate
   ```
   Confirm `DATABASE_URL` is supplied to this shell too; Vercel dashboard variables
   do not automatically configure your computer. Never run migrations per request.
   Migration `0002` seeds one category and three dishes and writes the bundled photo
   to `MEDIA_ROOT`, so the migration runner needs a writable media directory. That
   local photo is not automatically uploaded to Vercel. Migration `0003` records a
   pre-existing CAD help-text change only; existing migration history is retained.
6. Keep the seeded menu or import the reviewed local menu using the workflow below.
7. Create production accounts separately:
   ```powershell
   python manage.py createsuperuser
   ```
   Create staff accounts and permissions through admin. No development users transfer.
8. Verify HTTPS admin login, categories, item relationships, decimal pricing,
   ordering, status/availability, editing and the public menu. Image references need
   separately available media files; image storage has not been redesigned.
9. Redeploy again and verify the same menu edits and production accounts persist.

### Safe menu transfer for the next stage

No production transfer has been executed. Export only the two menu models from
SQLite in a **local development shell**, with `DATABASE_URL` absent:

```powershell
Remove-Item Env:DATABASE_URL -ErrorAction SilentlyContinue
$env:DJANGO_DEBUG = "true"
python manage.py dumpdata restaurant.MenuCategory restaurant.MenuItem --indent 2 --output menu-export.json
```

The fixture contains IDs, category relationships, ordering, prices, statuses,
slugs, descriptions, image paths and timestamps. It excludes users, sessions,
content types and migration records. Review and back up the file outside Git;
`menu-export.json` is ignored. Back up media separately: fixtures contain paths,
not image bytes. Avoid concurrent menu editing during export/import.

In a **separate production-configured shell** with `DATABASE_URL` securely set,
back up the target menu first (use the same `dumpdata` command with a different
output path outside the repository). Then:

```powershell
python manage.py import_menu menu-export.json
```

This command permits only menu records, checks that item categories are included,
and refuses any nonempty destination, including the migration seed menu. After
reviewing the backup and confirming replacement of the **entire** target menu:

```powershell
python manage.py import_menu menu-export.json --replace-menu
```

`--replace-menu` prints a warning and replaces all categories/items, including rows
absent from the fixture. It is not a merge. Replacement and Django `loaddata` run in
one transaction, rolling back on failure; database constraints are checked and
PostgreSQL ID sequences are reset. Repeating the same import restores the same
menu but overwrites intervening menu edits, so explicit consent is always required.
Users and other Django tables are not imported. Use only reviewed trusted fixtures;
Django fixture loading bypasses model `save()` and form/image validation.
Do not use unrestricted `loaddata` for this workflow.

### Database verification

With `DATABASE_URL` absent and local debug enabled:

```powershell
python manage.py check
python manage.py test
python manage.py makemigrations --check --dry-run
python manage.py migrate
python manage.py runserver
```

Normal tests use a separate SQLite test database and need no PostgreSQL server.
For this preparation, migrations are verified on disposable SQLite databases,
including a copy of the existing database, to keep the original byte-for-byte
unchanged. A live PostgreSQL migration test still needs a disposable hosted/local
PostgreSQL instance; configuration tests alone do not verify a server connection.

References: [dj-database-url](https://pypi.org/project/dj-database-url/),
[Psycopg installation](https://www.psycopg.org/psycopg3/docs/basic/install.html),
[Vercel Django support](https://vercel.com/changelog/zero-configuration-django-support).
