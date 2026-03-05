export interface DashboardData {
  today_cabbage_price: number | null
  today_potato_price: number | null
  top3_models: { product_name: string; model_name: string; mape: number | null }[]
  alert_unread_count: number
}

export interface SeriesItem {
  record_date: string
  price: number
  origin?: string
}

export interface CorrelationData {
  matrix: number[][]
  columns: string[]
}

export interface CompareItem {
  record_date: string
  product_name: string
  price: number
}

export interface AlertItem {
  id: number
  product_name: string
  record_date: string
  price: number | null
  alert_type: string
  reason: string | null
  is_read: number
  created_at?: string
}

export interface TrainResult {
  results: { model_name: string; mae?: number; rmse?: number; mape?: number; error?: string }[]
}

export interface PredictResult {
  product_name: string
  model_name: string
  metrics?: { model_name: string; mae: number; rmse: number; mape: number }
  predictions: { predict_date: string; price_pred: number; confidence_low?: number; confidence_high?: number }[]
}

export interface SingleModelPrediction {
  model_name: string
  metrics?: { model_name: string; mae: number; rmse: number; mape: number }
  predictions: { predict_date: string; price_pred: number; confidence_low?: number; confidence_high?: number }[]
  meta?: Record<string, number>
}

export interface MultiPredictResult {
  product_name: string
  results: SingleModelPrediction[]
}
