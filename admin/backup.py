import os
import csv
import shutil
import zipfile
from datetime import datetime
from flask import render_template, request, redirect, url_for, flash, send_file, jsonify
from includes.db import get_db_connection, query_db
from includes.auth import admin_required
from config.config import Config

# Folder where backups are stored
BACKUP_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'backups')

# Root of the project (one level above this file's directory)
PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))


def get_file_size(path):
    """Return human readable file size."""
    size = os.path.getsize(path)
    if size < 1024:
        return f"{size} B"
    elif size < 1024 * 1024:
        return f"{size // 1024} KB"
    else:
        return f"{size // (1024 * 1024)} MB"


@admin_required
def admin_backup_page():
    """Show backup/restore page with list of existing backups."""
    os.makedirs(BACKUP_DIR, exist_ok=True)

    backups = []
    for filename in sorted(os.listdir(BACKUP_DIR), reverse=True):
        if filename.endswith(('.zip', '.sql')):
            filepath = os.path.join(BACKUP_DIR, filename)
            stat     = os.stat(filepath)
            backups.append({
                'filename': filename,
                'name':     filename,
                'date':     datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M'),
                'size':     get_file_size(filepath)
            })

    return render_template('admin/backup.html', backups=backups)


@admin_required
def admin_create_backup():
    """Create a zip backup of the database and optionally uploads."""
    if request.method != 'POST':
        return redirect(url_for('admin_backup_page'))

    os.makedirs(BACKUP_DIR, exist_ok=True)

    include_uploads = request.form.get('include_uploads') == 'on'
    custom_name     = request.form.get('backup_name', '').strip()
    timestamp       = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_name     = f"{custom_name}_{timestamp}" if custom_name else f"backup_{timestamp}"
    zip_path        = os.path.join(BACKUP_DIR, f"{backup_name}.zip")

    try:
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            # --- Database ---
            db_path = Config.DATABASE_PATH
            if os.path.exists(db_path):
                zf.write(db_path, 'alchicken.db')

            if include_uploads:
                # --- General uploads folder ---
                uploads_dir = os.path.join(PROJECT_ROOT, 'uploads')
                if os.path.exists(uploads_dir):
                    for root, dirs, files in os.walk(uploads_dir):
                        for file in files:
                            file_path    = os.path.join(root, file)
                            archive_name = os.path.relpath(file_path, PROJECT_ROOT)
                            zf.write(file_path, archive_name)

                # --- Product images ---
                images_dir = Config.PRODUCT_IMG_DIR
                if os.path.exists(images_dir):
                    for root, dirs, files in os.walk(images_dir):
                        for file in files:
                            file_path    = os.path.join(root, file)
                            archive_name = os.path.relpath(file_path, PROJECT_ROOT)
                            zf.write(file_path, archive_name)

                # --- Payment proofs ---
                # Support both a dedicated Config attribute and a conventional path fallback
                payment_proofs_dir = getattr(Config, 'PAYMENT_PROOFS_DIR', None) or \
                                     os.path.join(PROJECT_ROOT, 'uploads', 'payment_proofs')
                if os.path.exists(payment_proofs_dir):
                    # Only add if it wasn't already captured under the uploads_dir walk above
                    if not payment_proofs_dir.startswith(os.path.join(PROJECT_ROOT, 'uploads')):
                        for root, dirs, files in os.walk(payment_proofs_dir):
                            for file in files:
                                file_path    = os.path.join(root, file)
                                archive_name = os.path.relpath(file_path, PROJECT_ROOT)
                                zf.write(file_path, archive_name)

        flash(f'Backup created successfully: {backup_name}.zip', 'success')
    except Exception as e:
        flash(f'Error creating backup: {str(e)}', 'danger')

    return redirect(url_for('admin_backup_page'))


@admin_required
def admin_restore_backup():
    """Restore database and media files from an uploaded backup zip file."""
    if request.method != 'POST':
        return redirect(url_for('admin_backup_page'))

    if 'backup_file' not in request.files or request.files['backup_file'].filename == '':
        flash('Please select a backup file to restore.', 'danger')
        return redirect(url_for('admin_backup_page'))

    file = request.files['backup_file']

    if not file.filename.endswith(('.zip', '.sql')):
        flash('Invalid file type. Please upload a .zip or .sql file.', 'danger')
        return redirect(url_for('admin_backup_page'))

    try:
        temp_path = os.path.join(BACKUP_DIR, 'temp_restore' + os.path.splitext(file.filename)[1])
        file.save(temp_path)

        if file.filename.endswith('.zip'):
            with zipfile.ZipFile(temp_path, 'r') as zf:
                namelist = zf.namelist()

                # ── 1. Restore database ──────────────────────────────────────
                if 'alchicken.db' in namelist:
                    db_path = Config.DATABASE_PATH
                    # Keep a safety copy of the current database
                    if os.path.exists(db_path):
                        shutil.copy2(db_path, db_path + '.pre_restore')
                    zf.extract('alchicken.db', os.path.dirname(db_path))
                else:
                    flash('No database file found in the zip backup.', 'danger')
                    os.remove(temp_path)
                    return redirect(url_for('admin_backup_page'))

                # ── 2. Restore product images ────────────────────────────────
                images_dir      = Config.PRODUCT_IMG_DIR
                images_rel_root = os.path.relpath(images_dir, PROJECT_ROOT)  # e.g. "static/img/products"

                restored_images = 0
                for member in namelist:
                    # Normalise separators so the check works on Windows too
                    norm = member.replace('\\', '/')
                    if norm.startswith(images_rel_root.replace('\\', '/') + '/'):
                        # Guard against path traversal
                        dest = os.path.realpath(os.path.join(PROJECT_ROOT, member))
                        if not dest.startswith(os.path.realpath(PROJECT_ROOT)):
                            continue
                        os.makedirs(os.path.dirname(dest), exist_ok=True)
                        with zf.open(member) as src, open(dest, 'wb') as out:
                            shutil.copyfileobj(src, out)
                        restored_images += 1

                # ── 3. Restore uploads folder (general + payment proofs) ─────
                uploads_dir = os.path.join(PROJECT_ROOT, 'uploads')
                uploads_rel = os.path.relpath(uploads_dir, PROJECT_ROOT)  # "uploads"

                # Also handle a standalone PAYMENT_PROOFS_DIR outside uploads/
                payment_proofs_dir = getattr(Config, 'PAYMENT_PROOFS_DIR', None)
                payment_rel        = None
                if payment_proofs_dir and not payment_proofs_dir.startswith(uploads_dir):
                    payment_rel = os.path.relpath(payment_proofs_dir, PROJECT_ROOT)

                restored_uploads = 0
                for member in namelist:
                    norm = member.replace('\\', '/')
                    is_upload  = norm.startswith(uploads_rel.replace('\\', '/') + '/')
                    is_payment = payment_rel and norm.startswith(payment_rel.replace('\\', '/') + '/')

                    if is_upload or is_payment:
                        dest = os.path.realpath(os.path.join(PROJECT_ROOT, member))
                        if not dest.startswith(os.path.realpath(PROJECT_ROOT)):
                            continue  # skip path-traversal attempts
                        os.makedirs(os.path.dirname(dest), exist_ok=True)
                        with zf.open(member) as src, open(dest, 'wb') as out:
                            shutil.copyfileobj(src, out)
                        restored_uploads += 1

                flash(
                    f'Restore complete — database, {restored_images} product image(s), '
                    f'and {restored_uploads} upload/proof file(s) restored successfully.',
                    'success'
                )

        else:
            # ── SQL file restore ─────────────────────────────────────────────
            db_path = Config.DATABASE_PATH
            conn    = get_db_connection()
            with open(temp_path, 'r') as f:
                conn.executescript(f.read())
            conn.close()
            flash('Database restored successfully from SQL backup.', 'success')

        os.remove(temp_path)

    except zipfile.BadZipFile:
        flash('The uploaded file is not a valid zip archive.', 'danger')
    except Exception as e:
        flash(f'Error restoring backup: {str(e)}', 'danger')

    return redirect(url_for('admin_backup_page'))


@admin_required
def admin_download_backup(filename):
    """Download a backup file."""
    # Sanitise filename to prevent directory traversal
    filename  = os.path.basename(filename)
    file_path = os.path.join(BACKUP_DIR, filename)

    if not os.path.exists(file_path):
        flash('Backup file not found.', 'danger')
        return redirect(url_for('admin_backup_page'))

    return send_file(file_path, as_attachment=True, download_name=filename)


@admin_required
def admin_delete_backup(filename):
    """Delete a backup file via POST/JSON."""
    filename  = os.path.basename(filename)
    file_path = os.path.join(BACKUP_DIR, filename)

    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'error': 'File not found'}), 404
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@admin_required
def admin_export_csv(type):
    """Export data as CSV file."""
    os.makedirs(BACKUP_DIR, exist_ok=True)

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename  = f"{type}_{timestamp}.csv"
    filepath  = os.path.join(BACKUP_DIR, filename)

    try:
        if type == 'customers':
            rows = query_db(
                "SELECT user_id, name, email, phone, address, role, created_at FROM users WHERE role = 'customer'"
            )
            headers = ['ID', 'Name', 'Email', 'Phone', 'Address', 'Role', 'Joined']

        elif type == 'orders':
            rows = query_db(
                """SELECT o.order_id, u.name, u.email, o.order_date, o.total_amount,
                          o.delivery_option, o.order_status, p.payment_method, p.payment_status
                   FROM orders o
                   JOIN users u ON o.user_id = u.user_id
                   LEFT JOIN payments p ON o.order_id = p.order_id
                   ORDER BY o.order_date DESC"""
            )
            headers = ['Order ID', 'Customer', 'Email', 'Date', 'Total',
                       'Delivery', 'Status', 'Payment Method', 'Payment Status']

        elif type == 'products':
            rows = query_db(
                "SELECT product_id, name, description, price, stock FROM products ORDER BY product_id"
            )
            headers = ['ID', 'Name', 'Description', 'Price (JMD)', 'Stock']

        elif type == 'sales':
            rows = query_db(
                """SELECT o.order_date, o.order_id, u.name, o.total_amount,
                          o.tax_amount, o.delivery_option, o.order_status
                   FROM orders o
                   JOIN users u ON o.user_id = u.user_id
                   WHERE o.order_status = 'completed'
                   ORDER BY o.order_date DESC"""
            )
            headers = ['Date', 'Order ID', 'Customer', 'Total (JMD)', 'Tax (JMD)', 'Delivery', 'Status']

        else:
            flash('Invalid export type.', 'danger')
            return redirect(url_for('admin_backup_page'))

        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(headers)
            for row in rows:
                writer.writerow(list(row))

        return send_file(filepath, as_attachment=True, download_name=filename,
                         mimetype='text/csv')

    except Exception as e:
        flash(f'Error exporting {type}: {str(e)}', 'danger')
        return redirect(url_for('admin_backup_page'))