# Pytest Fixture Philosophy

## Why Fixtures?
Unlike traditional xUnit `setup()` and `teardown()` methods, pytest fixtures are explicit, modular, and scalable.

### 1. Explicit Dependency Injection
Tests request fixtures by name. This makes it clear exactly what resources a test requires to function.

### 2. Composability
Fixtures can request other fixtures, allowing you to build complex environments from simple, reusable blocks.

```python
@pytest.fixture
def db_connection():
    return connect()

@pytest.fixture
def user_data(db_connection):
    # This fixture "composes" the db_connection fixture
    return db_connection.get_users()
```

### 3. Setup vs. Error
If a fixture fails during setup, pytest reports an **ERROR**, not a **FAILURE**. This distinction is critical:
- **FAILURE**: The test logic itself is broken.
- **ERROR**: The test environment could not be prepared.

## Best Practices
- **Minimal Dependencies**: Each test should only request the fixtures it strictly needs.
- **Avoid Global State**: Use fixtures with appropriate scopes (`function`, `module`, etc.) to ensure tests remain independent and repeatable.
- **Prefer Fixtures over `setup_module`**: Fixtures are more flexible and can be shared across multiple modules via `conftest.py`.
