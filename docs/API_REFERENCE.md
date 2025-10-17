# API Reference

## FastAPI Endpoints

### `POST /run_backtest`
- **Description:** Run a backtest with specified parameters.
- **Request Body:**
  - `tickers`: List[str]
  - `start_date`: str (YYYY-MM-DD)
  - `end_date`: str (YYYY-MM-DD)
  - `strategy`: str
- **Response:**
  - `results`: dict (metrics, trades, timeseries)

### `GET /results/{run_id}`
- **Description:** Retrieve results for a completed backtest.
- **Response:**
  - `results`: dict

### `GET /health`
- **Description:** Health check endpoint.
- **Response:**
  - `status`: str
