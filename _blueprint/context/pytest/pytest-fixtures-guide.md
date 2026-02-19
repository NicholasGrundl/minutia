# Pytest Fixtures Guide

## Core Concepts
Fixtures provide a fixed baseline upon which tests can reliably and repeatedly execute. They are the primary mechanism for dependency injection in pytest.

### 1. Requesting Fixtures
Tests request fixtures by naming them as arguments.

```python
@pytest.fixture
def fruit_bowl():
    return [Fruit("apple"), Fruit("banana")]

def test_fruit_salad(fruit_bowl):
    assert len(fruit_bowl) == 2
```

### 2. Fixture Scopes
Control how often a fixture is created and destroyed.
- `function` (default): Once per test function.
- `class`: Once per test class.
- `module`: Once per test module.
- `package`: Once per package.
- `session`: Once per test session.

```python
@pytest.fixture(scope="module")
def smtp_connection():
    return smtplib.SMTP("smtp.gmail.com")
```

### 3. Teardown with `yield`
The recommended pattern for cleanup.

```python
@pytest.fixture
def database():
    db = connect()
    yield db  # Provide the fixture value
    db.close() # Teardown code runs after the test
```

### 4. Fixture Factories
Use this pattern when you need multiple instances of an object with different configurations in one test.

```python
@pytest.fixture
def make_user():
    def _make_user(name):
        return User(name=name)
    return _make_user

def test_users(make_user):
    user1 = make_user("Alice")
    user2 = make_user("Bob")
```

## Best Practices
- **Atomicity**: Each fixture should perform exactly one state-changing action.
- **Modularity**: Fixtures can request other fixtures to build complex environments from simple parts.
- **`autouse=True`**: Use sparingly for "background" tasks like logging setup or temporary directory management.
- **`conftest.py`**: Place shared fixtures in `conftest.py` for automatic discovery across directories.
