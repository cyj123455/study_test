import client from './client'
import type { DashboardData, SeriesItem, CorrelationData, CompareItem, AlertItem, TrainResult, PredictResult, MultiPredictResult } from './types'

export const auth = {
  login: (username: string, password: string) =>
    client.post<{ access_token: string; user: { id: number; username: string; role: string } }>('/api/auth/login', { username, password }),
  register: (username: string, password: string) =>
    client.post('/api/auth/register', { username, password }),
}

export const dashboard = {
  get: () => client.get<DashboardData>('/api/dashboard'),
}

export const data = {
  listPrices: (params?: { product_name?: string; date_start?: string; date_end?: string; page?: number; page_size?: number }) =>
    client.get('/api/data/price', { params }),
  listWeather: (params?: { region?: string; date_start?: string; date_end?: string; page?: number; page_size?: number }) =>
    client.get('/api/data/weather', { params }),
  importPrice: (file: File) => {
    const form = new FormData()
    form.append('file', file)
    return client.post('/api/data/import/price', form, { headers: { 'Content-Type': 'multipart/form-data' } })
  },
  importWeather: (file: File) => {
    const form = new FormData()
    form.append('file', file)
    return client.post('/api/data/import/weather', form, { headers: { 'Content-Type': 'multipart/form-data' } })
  },
  crawl: (params?: { days_back?: number }) => client.post('/api/data/crawl', null, { params }),
  loadLocal: (params?: { clear_before?: boolean; remove_outliers?: boolean }) =>
    client.post<{ message: string; price_rows: number; weather_rows: number }>('/api/data/load-local', null, { params }),
  exportUrl: (dataType: string, params: { product_names?: string; date_start?: string; date_end?: string }) => {
    const q = new URLSearchParams({ data_type: dataType, ...params } as any)
    return `${import.meta.env.VITE_API_BASE || ''}/api/data/export?${q}`
  },
}

export const analysis = {
  series: (product_name: string, params?: { origin?: string; date_start?: string; date_end?: string; freq?: string }) =>
    client.get<SeriesItem[]>('/api/analysis/series', { params: { product_name, ...params } }),
  correlation: (product_name: string, params?: { origin?: string; date_start?: string; date_end?: string }) =>
    client.get<CorrelationData>('/api/analysis/correlation', { params: { product_name, ...params } }),
  compare: (product_names: string, params?: { date_start?: string; date_end?: string; freq?: string }) =>
    client.get<CompareItem[]>('/api/analysis/compare', { params: { product_names, ...params } }),
}

export const predict = {
  models: () => client.get<{ models: string[] }>('/api/predict/models'),
  train: (product_name: string, models: string[], train_ratio?: number, cv_folds?: number, ensemble_base_models?: string[]) =>
    client.post<TrainResult>('/api/predict/train', { product_name, models, train_ratio, cv_folds, ensemble_base_models }),
  predict: (product_name: string, model_name: string, predict_days?: number, use_weather?: boolean) =>
    client.post<PredictResult>('/api/predict/predict', { product_name, model_name, predict_days, use_weather }),
  predictMulti: (product_name: string, model_names: string[], predict_days?: number, use_weather?: boolean, ensemble_base_models?: string[]) =>
    client.post<MultiPredictResult>('/api/predict/predict-multi', { product_name, model_names, predict_days, use_weather, ensemble_base_models }),
}

export const alerts = {
  list: (params?: { product_name?: string; is_read?: number; limit?: number }) =>
    client.get<AlertItem[]>('/api/alerts', { params }),
  markRead: (alertId: number) => client.patch(`/api/alerts/${alertId}/read`),
}
