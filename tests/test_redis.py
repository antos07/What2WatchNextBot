import app.redis


def test_create_client():
    config = app.redis.Config(dsn="redis://url/1")

    client = app.redis.create_client(config)

    assert client.connection_pool.connection_kwargs["host"] == "url"
    assert client.connection_pool.connection_kwargs["port"] == 6379
    assert client.connection_pool.connection_kwargs["db"] == 1
