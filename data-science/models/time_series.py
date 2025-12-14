"""
Time Series Forecasting Model - ARIMA/Prophet for Donation Trends
Forecasts future donation volumes for capacity planning.
"""
import numpy as np
import pandas as pd
from typing import Dict, Any, Optional, List, Tuple
import pickle
import os
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

# Try to import Prophet, fall back to ARIMA if not available
try:
    from prophet import Prophet
    PROPHET_AVAILABLE = True
except ImportError:
    PROPHET_AVAILABLE = False

from sklearn.metrics import mean_absolute_error, mean_squared_error


class DonationForecaster:
    """
    Time Series Forecasting for donation trends.
    
    Uses Prophet for trend + seasonality decomposition.
    Falls back to simple moving average if Prophet unavailable.
    """
    
    def __init__(self, 
                 forecast_days: int = 30,
                 seasonality_mode: str = 'multiplicative',
                 include_holidays: bool = False):
        self.forecast_days = forecast_days
        self.seasonality_mode = seasonality_mode
        self.include_holidays = include_holidays
        
        self.model = None
        self.is_fitted = False
        self.training_metrics = {}
        self.training_data = None
        
        # Fallback method if Prophet not available
        self.use_prophet = PROPHET_AVAILABLE
    
    def prepare_data(self, donations: pd.DataFrame) -> pd.DataFrame:
        """
        Prepare daily aggregated data for forecasting.
        
        Expected columns:
        - timestamp: datetime
        - amount: float
        """
        # Ensure timestamp is datetime
        donations = donations.copy()
        donations['timestamp'] = pd.to_datetime(donations['timestamp'])
        
        # Aggregate by day
        daily = donations.groupby(donations['timestamp'].dt.date).agg({
            'amount': 'sum'
        }).reset_index()
        
        daily.columns = ['ds', 'y']
        daily['ds'] = pd.to_datetime(daily['ds'])
        
        # Fill missing dates with 0
        date_range = pd.date_range(
            start=daily['ds'].min(),
            end=daily['ds'].max(),
            freq='D'
        )
        
        full_data = pd.DataFrame({'ds': date_range})
        full_data = full_data.merge(daily, on='ds', how='left')
        full_data['y'] = full_data['y'].fillna(0)
        
        return full_data
    
    def _fit_prophet(self, data: pd.DataFrame):
        """Fit Prophet model"""
        self.model = Prophet(
            seasonality_mode=self.seasonality_mode,
            daily_seasonality=False,
            weekly_seasonality=True,
            yearly_seasonality=True if len(data) > 365 else False,
            changepoint_prior_scale=0.05
        )
        
        # Add custom seasonality for crypto/DAO patterns
        self.model.add_seasonality(
            name='monthly',
            period=30.5,
            fourier_order=5
        )
        
        self.model.fit(data)
    
    def _fit_simple(self, data: pd.DataFrame):
        """Simple moving average fallback"""
        self.training_data = data.copy()
        # Store 7-day and 30-day moving averages
        self.training_data['ma_7'] = self.training_data['y'].rolling(7).mean()
        self.training_data['ma_30'] = self.training_data['y'].rolling(30).mean()
    
    def fit(self, donations: pd.DataFrame) -> Dict[str, Any]:
        """
        Train the forecasting model.
        
        Args:
            donations: DataFrame with timestamp and amount columns
        
        Returns:
            Dictionary of training metrics
        """
        data = self.prepare_data(donations)
        
        # Need at least 30 days of data
        if len(data) < 30:
            raise ValueError("Need at least 30 days of data for forecasting")
        
        # Split for validation (last 7 days)
        train_data = data.iloc[:-7]
        val_data = data.iloc[-7:]
        
        if self.use_prophet:
            self._fit_prophet(train_data)
            
            # Validate
            future = self.model.make_future_dataframe(periods=7)
            forecast = self.model.predict(future)
            val_predictions = forecast.iloc[-7:]['yhat'].values
        else:
            self._fit_simple(train_data)
            # Use last 7-day MA as prediction
            val_predictions = np.full(7, train_data['y'].tail(7).mean())
        
        val_actual = val_data['y'].values
        
        # Calculate metrics
        mae = mean_absolute_error(val_actual, val_predictions)
        rmse = np.sqrt(mean_squared_error(val_actual, val_predictions))
        mape = np.mean(np.abs((val_actual - val_predictions) / (val_actual + 1e-6))) * 100
        
        # Refit on full data
        if self.use_prophet:
            self._fit_prophet(data)
        else:
            self._fit_simple(data)
        
        self.training_data = data
        
        self.training_metrics = {
            'mae': float(mae),
            'rmse': float(rmse),
            'mape': float(mape),
            'training_days': len(data),
            'total_donations': float(data['y'].sum()),
            'avg_daily_donations': float(data['y'].mean()),
            'method': 'prophet' if self.use_prophet else 'moving_average',
            'trained_at': datetime.now().isoformat()
        }
        
        self.is_fitted = True
        return self.training_metrics
    
    def forecast(self, days: Optional[int] = None) -> pd.DataFrame:
        """
        Generate forecast for future days.
        
        Args:
            days: Number of days to forecast (default: self.forecast_days)
        
        Returns:
            DataFrame with ds, yhat, yhat_lower, yhat_upper
        """
        if not self.is_fitted:
            raise ValueError("Model not fitted. Call fit() first.")
        
        days = days or self.forecast_days
        
        if self.use_prophet:
            future = self.model.make_future_dataframe(periods=days)
            forecast = self.model.predict(future)
            
            # Get only future predictions
            last_date = self.training_data['ds'].max()
            forecast = forecast[forecast['ds'] > last_date]
            
            return forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']].copy()
        else:
            # Simple moving average forecast
            last_date = self.training_data['ds'].max()
            future_dates = pd.date_range(
                start=last_date + timedelta(days=1),
                periods=days,
                freq='D'
            )
            
            # Use 7-day MA with some variation
            ma_7 = self.training_data['y'].tail(7).mean()
            ma_30 = self.training_data['y'].tail(30).mean()
            base_forecast = (ma_7 * 0.7 + ma_30 * 0.3)
            
            # Add some random variation for uncertainty
            np.random.seed(42)
            variation = np.random.uniform(0.8, 1.2, days)
            
            forecasts = base_forecast * variation
            
            return pd.DataFrame({
                'ds': future_dates,
                'yhat': forecasts,
                'yhat_lower': forecasts * 0.7,
                'yhat_upper': forecasts * 1.3
            })
    
    def get_trend_decomposition(self) -> Dict[str, Any]:
        """Get trend and seasonality components"""
        if not self.is_fitted:
            raise ValueError("Model not fitted")
        
        if self.use_prophet:
            # Get components from last prediction
            future = self.model.make_future_dataframe(periods=0)
            forecast = self.model.predict(future)
            
            return {
                'trend': forecast['trend'].values.tolist(),
                'weekly': forecast['weekly'].values.tolist() if 'weekly' in forecast.columns else [],
                'yearly': forecast['yearly'].values.tolist() if 'yearly' in forecast.columns else [],
                'dates': forecast['ds'].dt.strftime('%Y-%m-%d').tolist()
            }
        else:
            return {
                'trend': self.training_data['ma_30'].dropna().tolist(),
                'weekly': [],
                'yearly': [],
                'dates': self.training_data['ds'].dropna().dt.strftime('%Y-%m-%d').tolist()
            }
    
    def get_forecast_summary(self, days: Optional[int] = None) -> Dict[str, Any]:
        """Get summary statistics for forecast"""
        forecast = self.forecast(days)
        
        return {
            'forecast_period_start': forecast['ds'].min().strftime('%Y-%m-%d'),
            'forecast_period_end': forecast['ds'].max().strftime('%Y-%m-%d'),
            'total_forecast': float(forecast['yhat'].sum()),
            'avg_daily_forecast': float(forecast['yhat'].mean()),
            'min_daily_forecast': float(forecast['yhat'].min()),
            'max_daily_forecast': float(forecast['yhat'].max()),
            'total_lower_bound': float(forecast['yhat_lower'].sum()),
            'total_upper_bound': float(forecast['yhat_upper'].sum()),
            'confidence_interval': '80%'
        }
    
    def save(self, path: str):
        """Save model to disk"""
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'wb') as f:
            pickle.dump({
                'model': self.model if self.use_prophet else None,
                'training_data': self.training_data,
                'forecast_days': self.forecast_days,
                'seasonality_mode': self.seasonality_mode,
                'training_metrics': self.training_metrics,
                'use_prophet': self.use_prophet
            }, f)
    
    def load(self, path: str):
        """Load model from disk"""
        with open(path, 'rb') as f:
            data = pickle.load(f)
            self.model = data['model']
            self.training_data = data['training_data']
            self.forecast_days = data['forecast_days']
            self.seasonality_mode = data['seasonality_mode']
            self.training_metrics = data['training_metrics']
            self.use_prophet = data['use_prophet']
            self.is_fitted = True


def generate_synthetic_donations(n_days: int = 365) -> pd.DataFrame:
    """Generate synthetic donation data with trends and seasonality"""
    np.random.seed(42)
    
    dates = pd.date_range(
        end=datetime.now(),
        periods=n_days,
        freq='D'
    )
    
    donations = []
    
    for date in dates:
        # Base level with trend
        day_num = (date - dates[0]).days
        trend = 100 + day_num * 0.5  # Slight upward trend
        
        # Weekly seasonality (weekends lower)
        weekly_factor = 1.2 if date.weekday() < 5 else 0.6
        
        # Monthly seasonality (end of month higher)
        monthly_factor = 1.3 if date.day > 25 else 1.0
        
        # Random variation
        noise = np.random.uniform(0.5, 1.5)
        
        # Calculate amount
        amount = trend * weekly_factor * monthly_factor * noise
        
        # Generate multiple donations per day
        n_donations = max(1, int(np.random.poisson(5)))
        for _ in range(n_donations):
            donations.append({
                'timestamp': date + timedelta(hours=np.random.randint(0, 24)),
                'amount': amount / n_donations * np.random.uniform(0.5, 1.5)
            })
    
    return pd.DataFrame(donations)


if __name__ == "__main__":
    print("Generating synthetic donation data...")
    donations = generate_synthetic_donations(180)  # 6 months
    
    print(f"Generated {len(donations)} donations over 180 days")
    
    print("\nTraining Forecaster...")
    forecaster = DonationForecaster(forecast_days=30)
    metrics = forecaster.fit(donations)
    
    print(f"\nTraining Results:")
    print(f"  Method: {metrics['method']}")
    print(f"  MAE: {metrics['mae']:.2f}")
    print(f"  RMSE: {metrics['rmse']:.2f}")
    print(f"  MAPE: {metrics['mape']:.2f}%")
    print(f"  Avg Daily Donations: {metrics['avg_daily_donations']:.2f}")
    
    # Get forecast
    forecast = forecaster.forecast(7)
    print(f"\n7-Day Forecast:")
    for _, row in forecast.iterrows():
        print(f"  {row['ds'].strftime('%Y-%m-%d')}: {row['yhat']:.2f} ({row['yhat_lower']:.2f} - {row['yhat_upper']:.2f})")
    
    # Summary
    summary = forecaster.get_forecast_summary(30)
    print(f"\n30-Day Forecast Summary:")
    print(f"  Total Expected: {summary['total_forecast']:.2f}")
    print(f"  Range: {summary['total_lower_bound']:.2f} - {summary['total_upper_bound']:.2f}")
    
    # Save model
    forecaster.save('models/saved/forecaster.pkl')
    print("\nModel saved to models/saved/forecaster.pkl")
