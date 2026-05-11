# DynamoDB Schema Design

## 1) Generated Reports Table
- **Table name**: `stock-agent-generated-reports`
- **PK**: `pk` (`REPORT#{report_type}`)
- **SK**: `sk` (`TS#{generated_at_iso}`)
- **Attributes**: `report_id`, `payload`, `ttl`
- **Query pattern**:
  - Latest closing report
  - Historical reports by report type

## 2) Sentiment History Table
- **Table name**: `stock-agent-sentiment-history`
- **PK**: `pk` (`SENTIMENT`)
- **SK**: `sk` (`{timestamp_iso}`)
- **Attributes**: `report_type`, `sentiment`, `ttl`
- **Query pattern**:
  - Sentiment trend over time

## 3) Market Data Table (Optional Raw)
- **Table name**: `stock-agent-market-data`
- **PK**: `pk` (`MARKET#{date}`)
- **SK**: `sk` (`INDEX#{symbol}`)

## 4) News Table (Optional Raw)
- **Table name**: `stock-agent-news-items`
- **PK**: `pk` (`NEWS#{date}`)
- **SK**: `sk` (`ITEM#{news_id}`)
- **GSI suggestion**: `ticker-index` on `ticker` + `published_at`

## 5) Earnings Table (Optional Raw)
- **Table name**: `stock-agent-earnings-reports`
- **PK**: `pk` (`EARNINGS#{ticker}`)
- **SK**: `sk` (`PERIOD#{quarter}`)
