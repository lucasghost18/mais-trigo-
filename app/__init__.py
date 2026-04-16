import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=False)
    app.config.from_mapping(
        SECRET_KEY=os.environ.get('SECRET_KEY', 'dev'),
        SQLALCHEMY_DATABASE_URI=os.environ.get('DATABASE_URL', 'sqlite:///orders.db'),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        PRINTER_METHOD=os.environ.get('PRINTER_METHOD', 'file'),
        PRINTER_OUTPUT_DIR=os.environ.get('PRINTER_OUTPUT_DIR'),
    )

    if test_config:
        app.config.update(test_config)

    db.init_app(app)

    with app.app_context():
        # import modules that register routes and models
        from . import models, routes
        # register blueprint from routes
        app.register_blueprint(routes.bp)
        db.create_all()

        # Simple migration: add unit_price to order items if missing (SQLite)
        try:
            from sqlalchemy import inspect, text
            inspector = inspect(db.engine)

            # order items migration
            table_name = models.OrderItem.__table__.name
            cols = [c['name'] for c in inspector.get_columns(table_name)]
            if 'unit_price' not in cols:
                if db.engine.url.drivername == 'sqlite':
                    db.session.execute(text(f'ALTER TABLE "{table_name}" ADD COLUMN unit_price FLOAT DEFAULT 0.0'))
                    db.session.commit()

            # order table migration: add customer address/vendor/notes fields if missing
            order_table = models.Order.__table__.name
            order_cols = [c['name'] for c in inspector.get_columns(order_table)]
            new_order_cols = (('address', 'TEXT'), ('city', 'TEXT'), ('phone', 'TEXT'), ('cnpj', 'TEXT'), ('vendor', 'TEXT'), ('notes', 'TEXT'))
            for col_name, col_type in new_order_cols:
                if col_name not in order_cols:
                    if db.engine.url.drivername == 'sqlite':
                        db.session.execute(text(f'ALTER TABLE "{order_table}" ADD COLUMN {col_name} {col_type}'))

            # add vendor_id column to link to Vendor table
            if 'vendor_id' not in order_cols:
                if db.engine.url.drivername == 'sqlite':
                    db.session.execute(text(f'ALTER TABLE "{order_table}" ADD COLUMN vendor_id INTEGER'))
            db.session.commit()

            # order items: add product_id column if missing
            items_table = models.OrderItem.__table__.name
            items_cols = [c['name'] for c in inspector.get_columns(items_table)]
            if 'product_id' not in items_cols:
                if db.engine.url.drivername == 'sqlite':
                    db.session.execute(text(f'ALTER TABLE "{items_table}" ADD COLUMN product_id INTEGER'))
            # add unit_weight column to order items if missing
            if 'unit_weight' not in items_cols:
                if db.engine.url.drivername == 'sqlite':
                    db.session.execute(text(f'ALTER TABLE "{items_table}" ADD COLUMN unit_weight FLOAT DEFAULT 0.0'))
            db.session.commit()

            # product table migration: add manufacturer if missing
            try:
                product_table = models.Product.__table__.name
                product_cols = [c['name'] for c in inspector.get_columns(product_table)]
                if 'manufacturer' not in product_cols:
                    if db.engine.url.drivername == 'sqlite':
                        db.session.execute(text(f'ALTER TABLE "{product_table}" ADD COLUMN manufacturer TEXT'))
                # add weight column to product table if missing
                if 'weight' not in product_cols:
                    if db.engine.url.drivername == 'sqlite':
                        db.session.execute(text(f'ALTER TABLE "{product_table}" ADD COLUMN weight FLOAT DEFAULT 0.0'))
                db.session.commit()
            except Exception:
                # if product table does not exist yet, ignore
                pass
        except Exception as e:
            app.logger.info(f'Migration check skipped or failed: {e}')

        # Ensure PRINTER_OUTPUT_DIR is absolute and exists
        outdir = app.config.get('PRINTER_OUTPUT_DIR')
        if not outdir:
            outdir = os.path.join(app.root_path, 'prints')
            app.config['PRINTER_OUTPUT_DIR'] = outdir
        elif not os.path.isabs(outdir):
            outdir = os.path.join(app.root_path, outdir)
            app.config['PRINTER_OUTPUT_DIR'] = outdir
        try:
            os.makedirs(app.config['PRINTER_OUTPUT_DIR'], exist_ok=True)
        except Exception:
            app.logger.info('Could not create prints output directory')

    return app
