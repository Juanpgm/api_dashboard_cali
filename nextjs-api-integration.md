# Next.js API Integration Guide

## API Configuration for Dashboard

The FastAPI backend is now fully configured with materialized views optimized for dashboard consumption.

### Base API URL

```javascript
const API_BASE_URL = "http://127.0.0.1:8000";
```

### Main Endpoints for Next.js Frontend

#### 1. Load All Materialized Views (Recommended for Dashboard)

```javascript
// GET /load_materialized_views/
const loadDashboardData = async () => {
  const response = await fetch(`${API_BASE_URL}/load_materialized_views/`);
  const data = await response.json();
  return data.materialized_views;
};
```

#### 2. Individual Dashboard Endpoints

##### Dashboard Metrics

```javascript
const getDashboardMetrics = async () => {
  const response = await fetch(`${API_BASE_URL}/dashboard/metrics/`);
  return await response.json();
};
```

##### Timeline Data

```javascript
const getTimelineData = async () => {
  const response = await fetch(`${API_BASE_URL}/dashboard/timeline/`);
  return await response.json();
};
```

##### Top Programs

```javascript
const getTopPrograms = async (limit = 10) => {
  const response = await fetch(
    `${API_BASE_URL}/dashboard/top_programs/?limit=${limit}`
  );
  return await response.json();
};
```

##### Centers Summary

```javascript
const getCentersSummary = async () => {
  const response = await fetch(`${API_BASE_URL}/dashboard/centers_summary/`);
  return await response.json();
};
```

##### Filter Options

```javascript
const getFilterOptions = async () => {
  const response = await fetch(`${API_BASE_URL}/dashboard/filters_options/`);
  return await response.json();
};
```

##### Paginated Projects with Filters

```javascript
const getProjectsPaginated = async (filters = {}) => {
  const params = new URLSearchParams();

  if (filters.page) params.append("page", filters.page);
  if (filters.size) params.append("size", filters.size);
  if (filters.search) params.append("search", filters.search);
  if (filters.center_filter)
    params.append("center_filter", filters.center_filter);
  if (filters.program_filter)
    params.append("program_filter", filters.program_filter);
  if (filters.year_filter) params.append("year_filter", filters.year_filter);

  const response = await fetch(
    `${API_BASE_URL}/dashboard/projects_paginated/?${params}`
  );
  return await response.json();
};
```

##### Yearly Comparison

```javascript
const getYearlyComparison = async () => {
  const response = await fetch(`${API_BASE_URL}/dashboard/yearly_comparison/`);
  return await response.json();
};
```

### Data Management Endpoints

#### Upload Data

```javascript
const uploadData = async (directoryPath) => {
  const formData = new FormData();
  formData.append("directory_path", directoryPath);

  const response = await fetch(
    `${API_BASE_URL}/upload_and_process_data_from/`,
    {
      method: "POST",
      body: formData,
    }
  );
  return await response.json();
};
```

#### Setup Dashboard (Initialize Materialized Views)

```javascript
const setupDashboard = async () => {
  const response = await fetch(`${API_BASE_URL}/setup_dashboard/`, {
    method: "POST",
  });
  return await response.json();
};
```

#### Refresh Materialized Views

```javascript
const refreshViews = async () => {
  const response = await fetch(`${API_BASE_URL}/refresh_materialized_views/`, {
    method: "POST",
  });
  return await response.json();
};
```

#### Check Database Info

```javascript
const getDatabaseInfo = async () => {
  const response = await fetch(`${API_BASE_URL}/database_info/`);
  return await response.json();
};
```

### Error Handling Example

```javascript
const apiCall = async (endpoint, options = {}) => {
  try {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, options);

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();
    return data;
  } catch (error) {
    console.error("API call failed:", error);
    throw error;
  }
};
```

### Next.js Hook Example

```javascript
import { useState, useEffect } from "react";

export const useDashboardData = () => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        const response = await fetch(
          "http://127.0.0.1:8000/load_materialized_views/"
        );
        const result = await response.json();

        if (result.status === "success") {
          setData(result.materialized_views);
        } else {
          throw new Error("Failed to load data");
        }
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  return { data, loading, error };
};
```

### Data Structure Examples

#### Dashboard Metrics Response

```json
{
  "total_proyectos": 1252,
  "total_centros_gestores": 27,
  "total_programas": 932,
  "total_ppto_inicial": 4551630898820.0,
  "total_ppto_modificado": 6359896403862.0,
  "total_ejecucion": 3976477722344.0,
  "total_pagos": 3448608990062.0,
  "ejecucion_porcentaje": 61.6,
  "pagos_porcentaje": 43.28
}
```

#### Timeline Data Response

```json
[
  {
    "anio": 2024,
    "periodo": "2024-01-31",
    "ppto_modificado": 2170787663303.0,
    "ejecucion": 301180963289.0,
    "pagos": 133107407486.0,
    "adiciones": 127669803671.0,
    "proyectos": 674,
    "registros": 674
  }
]
```

### Workflow for Frontend Integration

1. **First Time Setup:**

   ```javascript
   // Check if data exists
   const dbInfo = await getDatabaseInfo();

   // If no data, upload it first
   if (dbInfo.total_records === 0) {
     await uploadData("path/to/data/directory");
   }

   // Setup dashboard (create materialized views)
   await setupDashboard();
   ```

2. **Dashboard Loading:**

   ```javascript
   // Load all dashboard data at once
   const dashboardData = await loadDashboardData();

   // Or load individual components
   const metrics = await getDashboardMetrics();
   const timeline = await getTimelineData();
   const programs = await getTopPrograms(20);
   ```

3. **Data Updates:**

   ```javascript
   // When new data is uploaded, refresh views
   await uploadData("path/to/new/data");
   await refreshViews();

   // Reload dashboard
   const updatedData = await loadDashboardData();
   ```

### CORS Configuration (if needed)

If you encounter CORS issues, add this to your FastAPI main.py:

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Next.js default port
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Performance Recommendations

1. **Use materialized views endpoints** for dashboard data as they are pre-computed and fast
2. **Cache data** in Next.js using SWR or React Query
3. **Refresh materialized views** periodically or after data updates
4. **Use pagination** for large data sets (projects_paginated endpoint)
5. **Filter data** on the backend rather than frontend for better performance

The API is now ready for Next.js integration with optimized materialized views that provide fast, consistent data for your dashboard!
