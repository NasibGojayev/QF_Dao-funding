# DAO Quadratic Funding Platform - API Documentation

## Base URL

```
Production: https://api.yourdomain.com
Development: http://localhost:8000
```

## Authentication

All API endpoints require authentication using Token-based authentication.

### Obtain Token

**Endpoint:** `POST /api-token-auth/`

**Request:**
```json
{
  "username": "your_username",
  "password": "your_password"
}
```

**Response:**
```json
{
  "token": "9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b"
}
```

**Usage:**
```bash
curl -H "Authorization: Token 9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b" \
  http://localhost:8000/api/projects/
```

---

## Projects API

### List Projects

**Endpoint:** `GET /api/projects/`

**Query Parameters:**
- `page` (integer): Page number for pagination
- `search` (string): Search by title or description

**Response:**
```json
{
  "count": 42,
  "next": "http://localhost:8000/api/projects/?page=2",
  "previous": null,
  "results": [
    {
      "id": 1,
      "title": "Open Source Library",
      "description": "Building tools for developers",
      "owner": 1,
      "created_at": "2025-12-01T10:00:00Z",
      "metadata_uri": "ipfs://QmTest123"
    }
  ]
}
```

### Create Project

**Endpoint:** `POST /api/projects/`

**Request:**
```json
{
  "title": "My Project",
  "description": "Project description",
  "metadata_uri": "ipfs://QmMetadata"
}
```

**Response:** `201 Created`
```json
{
  "id": 2,
  "title": "My Project",
  "description": "Project description",
  "owner": 1,
  "created_at": "2025-12-08T14:00:00Z",
  "metadata_uri": "ipfs://QmMetadata"
}
```

### Get Project

**Endpoint:** `GET /api/projects/{id}/`

**Response:**
```json
{
  "id": 1,
  "title": "Open Source Library",
  "description": "Building tools for developers",
  "owner": 1,
  "created_at": "2025-12-01T10:00:00Z",
  "metadata_uri": "ipfs://QmTest123"
}
```

### Update Project

**Endpoint:** `PATCH /api/projects/{id}/`

**Request:**
```json
{
  "title": "Updated Title"
}
```

**Response:** `200 OK`

### Delete Project

**Endpoint:** `DELETE /api/projects/{id}/`

**Response:** `204 No Content`

---

## Rounds API

### List Rounds

**Endpoint:** `GET /api/rounds/`

**Response:**
```json
{
  "count": 3,
  "results": [
    {
      "id": 1,
      "name": "Spring 2025 Round",
      "start_at": "2025-03-01T00:00:00Z",
      "end_at": "2025-04-01T00:00:00Z"
    }
  ]
}
```

### Create Round

**Endpoint:** `POST /api/rounds/`

**Request:**
```json
{
  "name": "Summer 2025 Round",
  "start_at": "2025-06-01T00:00:00Z",
  "end_at": "2025-07-01T00:00:00Z"
}
```

**Response:** `201 Created`

### Get Round

**Endpoint:** `GET /api/rounds/{id}/`

---

## Grants API

### List Grants

**Endpoint:** `GET /api/grants/`

**Response:**
```json
{
  "count": 15,
  "results": [
    {
      "id": 1,
      "project": 1,
      "amount_requested": "5000.00"
    }
  ]
}
```

### Create Grant

**Endpoint:** `POST /api/grants/`

**Request:**
```json
{
  "project": 1,
  "amount_requested": "10000.00"
}
```

**Response:** `201 Created`

---

## Error Responses

### 400 Bad Request
```json
{
  "title": ["This field is required."]
}
```

### 401 Unauthorized
```json
{
  "detail": "Authentication credentials were not provided."
}
```

### 404 Not Found
```json
{
  "detail": "Not found."
}
```

### 500 Internal Server Error
```json
{
  "detail": "Internal server error."
}
```

---

## Rate Limiting

- **Limit:** 100 requests per minute per IP
- **Headers:**
  - `X-RateLimit-Limit`: Maximum requests
  - `X-RateLimit-Remaining`: Remaining requests
  - `X-RateLimit-Reset`: Reset timestamp

---

## Pagination

All list endpoints support pagination:

**Parameters:**
- `page`: Page number (default: 1)
- `page_size`: Items per page (default: 50, max: 100)

**Response:**
```json
{
  "count": 150,
  "next": "http://localhost:8000/api/projects/?page=2",
  "previous": null,
  "results": [...]
}
```

---

## Filtering & Search

### Search
```
GET /api/projects/?search=blockchain
```

### Ordering
```
GET /api/projects/?ordering=-created_at
```

---

## WebSocket API

### Events Stream

**Endpoint:** `ws://localhost:8001/ws/events`

**Messages:**
```json
{
  "type": "donation",
  "data": {
    "project_id": 1,
    "amount": "1.5",
    "donor": "0x1234..."
  }
}
```

---

## GraphQL API

**Endpoint:** `GET /graphql`

**Query Example:**
```graphql
query {
  projects {
    id
    title
    description
    owner {
      username
    }
  }
}
```

---

## Code Examples

### Python
```python
import requests

# Get token
response = requests.post('http://localhost:8000/api-token-auth/', {
    'username': 'user',
    'password': 'pass'
})
token = response.json()['token']

# List projects
headers = {'Authorization': f'Token {token}'}
projects = requests.get('http://localhost:8000/api/projects/', headers=headers)
print(projects.json())
```

### JavaScript
```javascript
// Get token
const response = await fetch('http://localhost:8000/api-token-auth/', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ username: 'user', password: 'pass' })
});
const { token } = await response.json();

// List projects
const projects = await fetch('http://localhost:8000/api/projects/', {
  headers: { 'Authorization': `Token ${token}` }
});
console.log(await projects.json());
```

### cURL
```bash
# Get token
TOKEN=$(curl -X POST http://localhost:8000/api-token-auth/ \
  -H "Content-Type: application/json" \
  -d '{"username":"user","password":"pass"}' \
  | jq -r '.token')

# List projects
curl -H "Authorization: Token $TOKEN" \
  http://localhost:8000/api/projects/
```

---

*Last updated: December 8, 2025*
