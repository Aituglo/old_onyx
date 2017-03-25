# -*- coding: utf-8 -*-
"""Test configs."""
from onyx.app import create_app
from onyx.flask_config import DevConfig, ProdConfig


def test_production_config():
    """Production config."""
    app = create_app(config=ProdConfig)
    assert app.config['ENV'] == 'prod'
    assert app.config['DEBUG'] is False
    assert app.config['DEBUG_TB_ENABLED'] is False
    assert app.config['ASSETS_DEBUG'] is False


def test_dev_config():
    """Development config."""
    app = create_app(config=DevConfig)
    assert app.config['ENV'] == 'dev'
    assert app.config['DEBUG'] is True
    assert app.config['ASSETS_DEBUG'] is True