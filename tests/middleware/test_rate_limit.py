import pytest
import httpx


@pytest.mark.asyncio
async def test_login_allows_first_five_requests(test_app):
    transport = httpx.ASGITransport(
        app=test_app,
        client=("127.0.0.1", 8000),
    )

    async with httpx.AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as client:

        for _ in range(5):
            response = await client.post(
                "/api/v1/auth/login"
            )

            assert response.status_code == 200


@pytest.mark.asyncio
async def test_login_rejects_sixth_request(test_app):
    transport = httpx.ASGITransport(
        app=test_app,
        client=("127.0.0.1", 8000),
    )

    async with httpx.AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as client:

        for _ in range(5):
            await client.post("/api/v1/auth/login")

        response = await client.post(
            "/api/v1/auth/login"
        )

        assert response.status_code == 429

        assert response.json() == {
            "details": "Too many requests. Please try again later."
        }

        assert "Retry-After" in response.headers


@pytest.mark.asyncio
async def test_different_ips_have_separate_limits(test_app):
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(
            app=test_app,
            client=("127.0.0.1", 8001),
        ),
        base_url="http://test",
    ) as client_one:

        for _ in range(5):
            response = await client_one.post(
                "/api/v1/auth/login"
            )
            assert response.status_code == 200

        response = await client_one.post(
            "/api/v1/auth/login"
        )
        assert response.status_code == 429

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(
            app=test_app,
            client=("127.0.0.2", 8002),
        ),
        base_url="http://test",
    ) as client_two:

        response = await client_two.post(
            "/api/v1/auth/login"
        )

        assert response.status_code == 200


@pytest.mark.asyncio
async def test_health_endpoint_is_excluded(test_app):
    transport = httpx.ASGITransport(app=test_app)

    async with httpx.AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as client:

        for _ in range(10):
            response = await client.get("/health")
            assert response.status_code == 200


@pytest.mark.asyncio
async def test_general_api_has_rate_limit_headers(test_app):
    transport = httpx.ASGITransport(app=test_app)

    async with httpx.AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as client:

        response = await client.get(
            "/api/v1/employees"
        )

        assert response.status_code == 200
        assert response.headers["X-RateLimit-Limit"] == "100"
        assert response.headers["X-RateLimit-Remaining"] == "99"


@pytest.mark.asyncio
async def test_redis_failure_does_not_block_request(test_app):
    class BrokenRedis:
        async def eval(self, *args, **kwargs):
            raise ConnectionError("Redis unavailable")

    test_app.state.redis = BrokenRedis()

    transport = httpx.ASGITransport(app=test_app)

    async with httpx.AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as client:

        response = await client.get(
            "/api/v1/employees"
        )

        assert response.status_code == 200