import numpy as np
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
from datetime import datetime, timedelta
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tsa.statespace.sarimax import SARIMAX
from sklearn.linear_model import LinearRegression
import yfinance as yf

@st.cache_data(ttl=1800)
def generate_price_prediction(hist_data, forecast_days=30, model_type="linear"):
    """
    Generate price prediction with confidence intervals
    
    Args:
        hist_data (pd.DataFrame): Historical price data
        forecast_days (int): Number of days to forecast
        model_type (str): Type of model to use ('arima', 'linear', or 'sarimax')
        
    Returns:
        dict: Dictionary with forecast data and model information
    """
    try:
        # Make sure we have some data, but don't require as many points
        if len(hist_data) < 10:
            return {
                "success": False,
                "error": "Need at least 10 days of price data for prediction"
            }
        
        # Extract the closing prices
        close_prices = hist_data['Close'].values
        
        # Convert dates to numbers for prediction calculations to avoid timestamp arithmetic errors
        date_indices = np.arange(len(hist_data))
        forecast_indices = np.arange(len(hist_data), len(hist_data) + forecast_days)
        
        # For display purposes only, create business day date labels
        if isinstance(hist_data.index, pd.DatetimeIndex):
            last_date = hist_data.index[-1]
            # Create dates for display, using business day frequency
            forecast_dates = pd.date_range(start=last_date, periods=forecast_days + 1, freq='B')[1:]
        else:
            # If index is not datetime, create a simple numeric forecast
            forecast_dates = pd.date_range(start=pd.Timestamp.now(), periods=forecast_days, freq='B')
        
        if model_type == "linear":
            # Simple linear regression model using integer indices instead of timestamps
            X = date_indices.reshape(-1, 1)
            y = close_prices
            
            model = LinearRegression()
            model.fit(X, y)
            
            # Generate forecast using integer indices
            X_forecast = forecast_indices.reshape(-1, 1)
            forecast_mean = model.predict(X_forecast)
            
            # Calculate standard error to create confidence intervals
            y_pred = model.predict(X)
            residuals = y - y_pred
            std_error = np.std(residuals)
            
            # 95% confidence interval (approximately 2 standard deviations)
            lower_ci = forecast_mean - 1.96 * std_error
            upper_ci = forecast_mean + 1.96 * std_error
            
            model_name = "Linear Regression"
        
        elif model_type == "arima":
            try:
                # Try to fit ARIMA model using integer indices
                # Use simpler model to avoid timestamp issues
                from statsmodels.tsa.ar_model import AutoReg
                model = AutoReg(close_prices, lags=3)
                model_fit = model.fit()
                
                # Generate forecast using predict method
                forecast_mean = model_fit.predict(start=len(close_prices), end=len(close_prices) + forecast_days - 1)
                
                # Simple confidence interval based on volatility
                std_dev = np.std(close_prices)
                factor = np.sqrt(np.arange(1, forecast_days + 1)) * 0.5
                
                # Calculate confidence intervals
                lower_ci = forecast_mean - 1.96 * std_dev * factor
                upper_ci = forecast_mean + 1.96 * std_dev * factor
                
                model_name = "AutoRegressive(3)"
            except Exception as e:
                # Fallback to polynomial if AR fails
                x = date_indices
                poly_coefs = np.polyfit(x, close_prices, 2)
                
                # Generate forecast using integer indices
                forecast_mean = np.polyval(poly_coefs, forecast_indices)
                
                # Confidence intervals
                std_dev = np.std(close_prices)
                lower_ci = forecast_mean - 1.96 * std_dev
                upper_ci = forecast_mean + 1.96 * std_dev
                
                model_name = "Polynomial Trend"
                
        else:  # Default to exponential smoothing
            # Simple exponential smoothing - using integer indices
            alpha = 0.3  # Smoothing factor
            
            # Initialize with starting point
            forecast_mean = np.zeros(forecast_days)
            forecast_mean[0] = close_prices[-1]  
            
            # Generate forecast
            for i in range(1, forecast_days):
                forecast_mean[i] = alpha * forecast_mean[i-1] + (1-alpha) * close_prices[-1]
            
            # Calculate standard error for confidence intervals
            std_dev = np.std(close_prices)
            factor = np.sqrt(np.arange(1, forecast_days + 1)) * 0.4  # Lower factor for tighter bounds
            
            # 95% confidence interval
            lower_ci = forecast_mean - 1.96 * std_dev * factor
            upper_ci = forecast_mean + 1.96 * std_dev * factor
            
            model_name = "Exponential Smoothing"
        
        # Prepare result dictionary with forecast data
        result = {
            "success": True,
            "forecast_dates": forecast_dates,
            "forecast_mean": forecast_mean,
            "lower_ci": lower_ci,
            "upper_ci": upper_ci,
            "model": model_name,
            "last_price": close_prices[-1],
            "hist_dates": hist_data.index,
            "hist_prices": close_prices
        }
        
        return result
        
    except Exception as e:
        # If any error occurs, return simple error message
        return {
            "success": False,
            "error": "Could not generate prediction. Please try a different model or time period."
        }

def create_prediction_chart(prediction_data, company_name, currency="$"):
    """
    Create an animated prediction chart with confidence intervals
    
    Args:
        prediction_data (dict): Prediction data from generate_price_prediction
        company_name (str): Name of the company for chart title
        currency (str): Currency symbol ($, ₹, etc.)
        
    Returns:
        plotly.graph_objects.Figure: Plotly figure with prediction chart
    """
    if not prediction_data["success"]:
        # Return empty figure with error message
        fig = go.Figure()
        fig.add_annotation(
            text=f"Prediction Error: {prediction_data['error']}",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=14)
        )
        return fig
    
    # Extract data from prediction result
    hist_dates = prediction_data["hist_dates"]
    hist_prices = prediction_data["hist_prices"]
    forecast_dates = prediction_data["forecast_dates"]
    forecast_mean = prediction_data["forecast_mean"]
    lower_ci = prediction_data["lower_ci"]
    upper_ci = prediction_data["upper_ci"]
    model_name = prediction_data["model"]
    
    # Create figure
    fig = go.Figure()
    
    # Add historical price line
    fig.add_trace(
        go.Scatter(
            x=hist_dates,
            y=hist_prices,
            mode='lines',
            name='Historical Price',
            line=dict(color='royalblue', width=2)
        )
    )
    
    # Add forecast line
    fig.add_trace(
        go.Scatter(
            x=forecast_dates,
            y=forecast_mean,
            mode='lines',
            name='Price Forecast',
            line=dict(color='firebrick', width=2, dash='dash')
        )
    )
    
    # Add confidence interval as a shaded area
    fig.add_trace(
        go.Scatter(
            x=forecast_dates.tolist() + forecast_dates.tolist()[::-1],
            y=upper_ci.tolist() + lower_ci.tolist()[::-1],
            fill='toself',
            fillcolor='rgba(231,107,243,0.2)',
            line=dict(color='rgba(255,255,255,0)'),
            name='95% Confidence Interval',
            showlegend=True
        )
    )
    
    # Add vertical line separating historical data and forecast
    last_date = hist_dates[-1]
    
    fig.add_vline(
        x=last_date, 
        line_width=1.5, 
        line_dash="dash", 
        line_color="gray",
        annotation_text="Forecast Start",
        annotation_position="top right"
    )
    
    # Format the chart
    fig.update_layout(
        title=f"{company_name} Stock Price Prediction ({model_name})",
        xaxis_title="Date",
        yaxis_title=f"Price ({currency})",
        hovermode="x unified",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="center",
            x=0.5
        ),
        # For animation
        updatemenus=[dict(
            type="buttons",
            buttons=[dict(
                label="Play Forecast",
                method="animate",
                args=[None, dict(
                    frame=dict(duration=100, redraw=True),
                    fromcurrent=True,
                    transition=dict(duration=0)
                )]
            )]
        )]
    )
    
    # Create frames for animation
    frames = []
    
    # Total number of days to animate
    n_forecast_days = len(forecast_dates)
    
    for i in range(1, n_forecast_days + 1):
        frame_data = [
            # Historical line (unchanged)
            go.Scatter(
                x=hist_dates,
                y=hist_prices,
                mode='lines',
                name='Historical Price',
                line=dict(color='royalblue', width=2)
            ),
            # Forecast line (growing)
            go.Scatter(
                x=forecast_dates[:i],
                y=forecast_mean[:i],
                mode='lines',
                name='Price Forecast',
                line=dict(color='firebrick', width=2, dash='dash')
            ),
            # Confidence interval (growing) - using string dates to avoid timestamp arithmetic
            go.Scatter(
                x=list(forecast_dates[:i].strftime('%Y-%m-%d')) + list(forecast_dates[:i].strftime('%Y-%m-%d'))[::-1],
                y=upper_ci[:i].tolist() + lower_ci[:i].tolist()[::-1],
                fill='toself',
                fillcolor='rgba(231,107,243,0.2)',
                line=dict(color='rgba(255,255,255,0)'),
                name='95% Confidence Interval',
                showlegend=True
            )
        ]
        
        frames.append(go.Frame(data=frame_data, name=f"frame{i}"))
    
    fig.frames = frames
    
    return fig

def display_prediction_section(stock_symbol, hist_data, company_name, is_indian=False):
    """
    Display the prediction section in the Streamlit app
    
    Args:
        stock_symbol (str): Stock symbol
        hist_data (pd.DataFrame): Historical price data
        company_name (str): Company name
        is_indian (bool): Whether it's an Indian stock
    """
    st.subheader("📈 Price Prediction & Forecast")
    
    # Check if we have enough data points first
    if len(hist_data) < 10:
        st.warning("Not enough historical data available for prediction. Try selecting a longer time period.")
        return
    
    # Make sure index is datetime format
    if not isinstance(hist_data.index, pd.DatetimeIndex):
        try:
            hist_data.index = pd.to_datetime(hist_data.index)
        except:
            st.error("Could not process date information in the historical data.")
            return
    
    # Options for prediction settings
    col1, col2 = st.columns([1, 1])
    
    with col1:
        # Limit max forecast days based on data size
        max_days = min(90, len(hist_data))
        default_days = min(30, max_days // 2)
        step = max(1, max_days // 10)
        
        forecast_days = st.slider(
            "Forecast Days", 
            min_value=7, 
            max_value=max_days, 
            value=default_days, 
            step=step,
            help="Number of days to forecast into the future"
        )
    
    with col2:
        model_type = st.selectbox(
            "Prediction Model",
            ["linear", "arima", "smoothing"],  # Default to linear as most reliable
            format_func=lambda x: {
                "arima": "ARIMA (Time Series)",
                "smoothing": "Exponential Smoothing",
                "linear": "Linear Regression"
            }.get(x, x),
            help="Select the forecasting model to use"
        )
    
    # Generate prediction with a progress indicator
    with st.spinner("Generating price prediction..."):
        # Use a try-except block for additional error handling
        try:
            prediction = generate_price_prediction(hist_data, forecast_days, model_type)
            
            # Set currency based on whether it's an Indian stock
            currency = "₹" if is_indian else "$"
            
            # Create and display the prediction chart
            fig = create_prediction_chart(prediction, company_name, currency)
            st.plotly_chart(fig, use_container_width=True)
        
            # Display prediction insights
            if prediction["success"]:
                last_price = prediction["last_price"]
                forecast_end_price = prediction["forecast_mean"][-1]
                change_pct = ((forecast_end_price - last_price) / last_price) * 100
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Current Price", f"{currency} {last_price:.2f}", delta=None)
                
                with col2:
                    st.metric(f"Predicted Price ({forecast_days} days)", 
                            f"{currency} {forecast_end_price:.2f}", 
                            f"{change_pct:.2f}%")
                
                with col3:
                    confidence_range = f"{currency} {prediction['lower_ci'][-1]:.2f} - {currency} {prediction['upper_ci'][-1]:.2f}"
                    st.metric("95% Confidence Range", confidence_range)
                
                # Add prediction disclaimer
                st.info("""
                **Disclaimer:** This price prediction is for educational purposes only and should not be used as financial advice. 
                The models are simple forecasts based on historical patterns and do not account for news events, earnings, or market sentiment.
                """)
            else:
                st.error(f"Failed to generate prediction: {prediction['error']}")
                st.info("Try selecting a different prediction model or adjust the time period for analysis.")
        except Exception as e:
            st.error(f"An error occurred while generating the prediction: {str(e)}")
            st.info("Try using a different prediction model or select a different stock/time period.")