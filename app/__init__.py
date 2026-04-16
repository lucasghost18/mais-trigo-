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
        PRINTER_OUTPUT_DIR=os.environ.get('PRINTER_OUTPUT_DIR', 'prints'),
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
                    db.session.execute(text(f'ALTER TABLE {table_name} ADD COLUMN unit_price FLOAT DEFAULT 0.0'))
                    db.session.commit()

            # order table migration: add customer address fields if missing
            order_table = models.Order.__table__.name
            order_cols = [c['name'] for c in inspector.get_columns(order_table)]
            for col_name, col_type in (('address', 'TEXT'), ('city', 'TEXT'), ('phone', 'TEXT'), ('cnpj', 'TEXT')):
                if col_name not in order_cols:
                    if db.engine.url.drivername == 'sqlite':
                        db.session.execute(text(f'ALTER TABLE {order_table} ADD COLUMN {col_name} {col_type}'))
            db.session.commit()
        except Exception as e:
            app.logger.info(f'Migration check skipped or failed: {e}')

    return app
