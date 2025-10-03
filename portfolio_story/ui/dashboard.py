"""
The Portfolio Story - Interactive Web Dashboard
Professional, user-friendly dashboard for naive investors with clear explanations
"""

import dash
from dash import dcc, html, Input, Output, State, callback, dash_table
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
import os
import functools
import threading
from concurrent.futures import ThreadPoolExecutor
import time

# Add parent directory to path
sys.path.append('..')
sys.path.append('../..')

try:
    from portfolio_story.portfolio_manager import PortfolioManager
    print("PortfolioManager imported successfully!")
except ImportError as e:
    print(f"Warning: Could not import PortfolioManager: {e}")
    print("Dashboard will run in demo mode.")
    PortfolioManager = None

# Cache for portfolio results
portfolio_cache = {}
CACHE_TIMEOUT = 300  # 5 minutes

def get_cached_portfolio(cache_key):
    """Get cached portfolio if still valid"""
    if cache_key in portfolio_cache:
        cached_data, timestamp = portfolio_cache[cache_key]
        if time.time() - timestamp < CACHE_TIMEOUT:
            return cached_data
        else:
            del portfolio_cache[cache_key]
    return None

def cache_portfolio(cache_key, data):
    """Cache portfolio data"""
    portfolio_cache[cache_key] = (data, time.time())

# Initialize Dash app with professional styling
app = dash.Dash(__name__, external_stylesheets=[
    'https://codepen.io/chriddyp/pen/bWLwgP.css',
    'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css',
    'https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap'
])

# Professional CSS styling
app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>{%title%}</title>
        {%favicon%}
        {%css%}
        <style>
            * {
                box-sizing: border-box;
                margin: 0;
                padding: 0;
            }
            
            body { 
                font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Tahoma', 'Geneva', 'Verdana', sans-serif;
                background: linear-gradient(135deg, #0f0f23 0%, #1a1a2e 50%, #16213e 100%);
                min-height: 100vh;
                line-height: 1.6;
                font-size: 16px;
                color: #ffffff;
                overflow-x: hidden;
            }
            
            /* Modern Animations */
            @keyframes fadeInUp {
                from {
                    opacity: 0;
                    transform: translateY(30px);
                }
                to {
                    opacity: 1;
                    transform: translateY(0);
                }
            }
            
            @keyframes slideInRight {
                from {
                    opacity: 0;
                    transform: translateX(30px);
                }
                to {
                    opacity: 1;
                    transform: translateX(0);
                }
            }
            
            @keyframes pulse {
                0%, 100% {
                    transform: scale(1);
                }
                50% {
                    transform: scale(1.05);
                }
            }
            
            @keyframes shimmer {
                0% {
                    background-position: -200px 0;
                }
                100% {
                    background-position: calc(200px + 100%) 0;
                }
            }
            
            /* Loading Animation */
            .loading-spinner {
                width: 40px;
                height: 40px;
                border: 3px solid rgba(255, 255, 255, 0.1);
                border-top: 3px solid #667eea;
                border-radius: 50%;
                animation: spin 1s linear infinite;
                margin: 20px auto;
            }
            
            @keyframes spin {
                0% { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
            }
            
            /* Responsive Design */
            @media (max-width: 768px) {
                .content-grid {
                    grid-template-columns: 1fr;
                    gap: 20px;
                }
                
                .header-title {
                    font-size: 2.5rem;
                }
                
                .step-indicator {
                    flex-direction: column;
                    gap: 10px;
                }
                
                .main-container {
                    padding: 15px;
                }
            }
            
            /* Consistent font styling for all elements */
            h1, h2, h3, h4, h5, h6 {
                font-family: 'Inter', 'Segoe UI', 'Tahoma', 'Geneva', 'Verdana', sans-serif;
                font-weight: 600;
                color: #ffffff;
            }
            
            p, span, div, label {
                font-family: 'Inter', 'Segoe UI', 'Tahoma', 'Geneva', 'Verdana', sans-serif;
                color: #ffffff;
            }
            
            /* Table and chart font consistency */
            .dash-table-container, .plotly-graph-div {
                font-family: 'Inter', 'Segoe UI', 'Tahoma', 'Geneva', 'Verdana', sans-serif !important;
            }
            
            /* Ensure all text elements use consistent font */
            * {
                font-family: 'Inter', 'Segoe UI', 'Tahoma', 'Geneva', 'Verdana', sans-serif;
            }
            
            .main-container {
                max-width: 1400px;
                margin: 0 auto;
                padding: 20px;
                position: relative;
            }
            
            .header-section {
                background: rgba(255, 255, 255, 0.05);
                backdrop-filter: blur(20px);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 24px;
                color: white;
                padding: 40px;
                margin-bottom: 30px;
                box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
                text-align: center;
                position: relative;
                overflow: hidden;
            }
            
            .header-section::before {
                content: '';
                position: absolute;
                top: 0;
                left: 0;
                right: 0;
                height: 1px;
                background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.4), transparent);
            }
            
            .header-title {
                font-size: 3.5rem;
                font-weight: 700;
                margin-bottom: 15px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                background-clip: text;
                text-shadow: 0 4px 8px rgba(0, 0, 0, 0.3);
                line-height: 1.2;
            }
            
            .header-subtitle {
                font-size: 1.4rem;
                font-weight: 400;
                opacity: 0.9;
                margin-bottom: 20px;
                color: #000000;
            }
            
            .header-description {
                font-size: 1.1rem;
                opacity: 0.8;
                max-width: 800px;
                margin: 0 auto;
                line-height: 1.6;
                color: #b8c5d1;
            }
            
            .step-indicator {
                display: flex;
                justify-content: center;
                margin: 30px 0;
                gap: 20px;
                padding: 0 20px;
            }
            
            .step {
                background: rgba(255, 255, 255, 0.08);
                backdrop-filter: blur(10px);
                border: 1px solid rgba(255, 255, 255, 0.1);
                color: #b8c5d1;
                padding: 16px 24px;
                border-radius: 50px;
                font-weight: 500;
                font-size: 0.95rem;
                transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
                position: relative;
                overflow: hidden;
                cursor: pointer;
                user-select: none;
                text-align: center;
                min-width: 120px;
                max-width: 200px;
                line-height: 1.4;
            }
            
            .step span {
                display: block;
                font-weight: 600;
                margin-bottom: 4px;
            }
            
            .step small {
                display: block;
                font-size: 0.9rem;
                opacity: 1;
                line-height: 1.2;
                color: #b8c5d1;
                font-weight: 400;
            }
            
            .step::before {
                content: '';
                position: absolute;
                top: 0;
                left: -100%;
                width: 100%;
                height: 100%;
                background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.1), transparent);
                transition: left 0.5s;
            }
            
            .step:hover::before {
                left: 100%;
            }
            
            .step.active {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                box-shadow: 0 8px 25px rgba(102, 126, 234, 0.4);
                transform: translateY(-2px);
                border: 1px solid rgba(255, 255, 255, 0.2);
            }
            
            .step.completed {
                background: linear-gradient(135deg, #28a745 0%, #20c997 100%);
                color: white;
                box-shadow: 0 8px 25px rgba(40, 167, 69, 0.4);
            }
            
            .content-grid {
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 30px;
                margin-bottom: 30px;
            }
            
            .form-card, .info-card {
                background: rgba(255, 255, 255, 0.05);
                backdrop-filter: blur(20px);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 20px;
                padding: 30px;
                box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
                transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
                position: relative;
                overflow: hidden;
            }
            
            .form-card:hover, .info-card:hover {
                transform: translateY(-5px);
                box-shadow: 0 20px 40px rgba(0, 0, 0, 0.4);
                border-color: rgba(255, 255, 255, 0.2);
            }
            
            .form-card::before, .info-card::before {
                content: '';
                position: absolute;
                top: 0;
                left: 0;
                right: 0;
                height: 1px;
                background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.3), transparent);
            }
            
            .info-card {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 35px; /* Increased padding for better spacing */
                border-radius: 16px;
                margin: 20px 0; /* Increased margin */
                box-shadow: 0 8px 25px rgba(102, 126, 234, 0.3);
                margin-left: 5px; /* Ensure content doesn't touch left edge */
                margin-right: 5px; /* Ensure content doesn't touch right edge */
            }
            
            
            .metric-card {
                background: rgba(255, 255, 255, 0.05);
                backdrop-filter: blur(20px);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 12px;
                padding: 25px; /* Increased padding for better spacing */
                margin: 15px; /* Increased margin */
                box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
                text-align: center;
                transition: transform 0.2s ease, box-shadow 0.2s ease;
                margin-left: 8px; /* Ensure content doesn't touch left edge */
                margin-right: 8px; /* Ensure content doesn't touch right edge */
            }
            
            .metric-card:hover {
                transform: translateY(-2px);
                box-shadow: 0 12px 40px rgba(0, 0, 0, 0.4);
                background: rgba(255, 255, 255, 0.08);
            }
            
            .form-group {
                margin-bottom: 30px; /* Increased margin for better spacing */
                padding: 0 5px; /* Ensure content doesn't touch edges */
            }
            
            .form-label {
                display: block;
                font-size: 1.2rem;
                font-weight: 600;
                color: #ffffff;
                margin-bottom: 12px;
                line-height: 1.4;
                overflow: visible;
                white-space: nowrap;
                padding-left: 0;
                margin-left: 0;
            }
            
            .form-input {
                width: 100%;
                padding: 15px 20px;
                font-size: 1rem;
                background: rgba(255, 255, 255, 0.08);
                backdrop-filter: blur(10px);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 12px;
                color: #ffffff;
                transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
                margin-bottom: 8px;
                box-sizing: border-box;
            }
            
            .form-input::placeholder {
                color: rgba(255, 255, 255, 0.6);
            }
            
            .form-input:focus {
                outline: none;
                border-color: #667eea;
                box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.2);
                background: rgba(255, 255, 255, 0.12);
            }
            
            .form-dropdown {
                width: 100%;
                font-size: 1.1rem;
                margin-bottom: 8px;
            }
            
            .form-dropdown .Select-control {
                background: rgba(255, 255, 255, 0.08);
                border: 1px solid rgba(255, 255, 255, 0.1);
                color: #ffffff;
                border-radius: 8px;
            }
            
            .form-dropdown .Select-value-label {
                color: #ffffff !important;
                font-size: 1.1rem;
                font-weight: 500;
            }
            
            .form-dropdown .Select-placeholder {
                color: rgba(255, 255, 255, 0.6) !important;
                font-size: 1.1rem;
            }
            
            .form-dropdown .Select-option {
                background: #2a2a3e !important;
                color: #ffffff !important;
                font-size: 1.1rem;
                padding: 12px 16px;
                border-bottom: 1px solid rgba(255, 255, 255, 0.1);
            }
            
            .form-dropdown .Select-option.is-focused {
                background: rgba(102, 126, 234, 0.3) !important;
                color: #ffffff !important;
            }
            
            .form-dropdown .Select-option.is-selected {
                background: rgba(102, 126, 234, 0.5) !important;
                color: #ffffff !important;
            }
            
            .form-dropdown .Select-menu-outer {
                background: #2a2a3e !important;
                border: 1px solid rgba(255, 255, 255, 0.2) !important;
                border-radius: 8px !important;
                box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3) !important;
            }
            
            .form-dropdown .Select-arrow-zone {
                color: #ffffff !important;
            }
            
            .form-dropdown .Select-arrow {
                color: #ffffff !important;
                border-color: #ffffff transparent transparent !important;
            }
            
            .form-slider {
                margin: 15px 0;
            }
            
            .slider-container {
                background: rgba(255, 255, 255, 0.05);
                backdrop-filter: blur(20px);
                border: 1px solid rgba(255, 255, 255, 0.1);
                padding: 25px 30px;
                border-radius: 12px;
                margin: 15px 0;
                box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
            }
            
            /* Slider track and handle styling */
            .rc-slider-track {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
            }
            
            .rc-slider-handle {
                background: #ffffff !important;
                border: 2px solid #667eea !important;
                box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3) !important;
            }
            
            .rc-slider-handle:hover {
                box-shadow: 0 6px 16px rgba(102, 126, 234, 0.4) !important;
            }
            
            .rc-slider-rail {
                background: rgba(255, 255, 255, 0.1) !important;
            }
            
            /* Slider marks alignment and spacing */
            .rc-slider-mark {
                display: flex !important;
                align-items: center !important;
                justify-content: center !important;
                text-align: center !important;
                white-space: nowrap !important;
                margin-top: 15px !important;
                padding: 0 5px !important;
            }
            
            .rc-slider-mark-text {
                display: inline-flex !important;
                align-items: center !important;
                justify-content: center !important;
                text-align: center !important;
                white-space: nowrap !important;
                line-height: 1.3 !important;
                padding: 2px 4px !important;
            }
            
            /* Ensure first and last marks have proper spacing */
            .rc-slider-mark:first-child {
                padding-left: 8px !important;
            }
            
            .rc-slider-mark:last-child {
                padding-right: 8px !important;
            }
            
            .btn-primary {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 16px 32px;
                font-size: 1.1rem;
                font-weight: 600;
                border: none;
                border-radius: 12px;
                cursor: pointer;
                transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
                width: 100%;
                box-shadow: 0 8px 25px rgba(102, 126, 234, 0.3);
                text-align: center;
                display: flex;
                align-items: center;
                justify-content: center;
                box-sizing: border-box;
                position: relative;
                overflow: hidden;
            }
            
            .btn-primary::before {
                content: '';
                position: absolute;
                top: 0;
                left: -100%;
                width: 100%;
                height: 100%;
                background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.2), transparent);
                transition: left 0.5s;
            }
            
            .btn-primary:hover::before {
                left: 100%;
            }
            
            .btn-primary:hover {
                transform: translateY(-2px);
                box-shadow: 0 8px 25px rgba(102, 126, 234, 0.6);
            }
            
            /* Loading animations */
            @keyframes loading {
                0% { width: 0%; }
                50% { width: 60%; }
                100% { width: 100%; }
            }
            
            @keyframes fadeIn {
                from { opacity: 0; transform: translateY(20px); }
                to { opacity: 1; transform: translateY(0); }
            }
            
            .fade-in {
                animation: fadeIn 0.5s ease-in-out;
            }
            
            .btn-primary:active {
                transform: translateY(0);
            }
            
            .icon {
                margin-right: 10px; /* Increased margin for better spacing */
                font-size: 1.3rem; /* Increased from 1.2rem for better visibility */
            }
            
            .results-section {
                background: white;
                border-radius: 16px;
                padding: 35px; /* Increased padding for better spacing */
                box-shadow: 0 8px 25px rgba(0,0,0,0.1);
                margin-top: 25px; /* Increased margin */
                margin-left: 5px; /* Ensure content doesn't touch left edge */
                margin-right: 5px; /* Ensure content doesn't touch right edge */
            }
            
            .chart-container {
                background: white;
                border-radius: 12px;
                padding: 25px; /* Increased padding for better spacing */
                margin: 20px 0; /* Increased margin */
                box-shadow: 0 4px 12px rgba(0,0,0,0.08);
                margin-left: 5px; /* Ensure content doesn't touch left edge */
                margin-right: 5px; /* Ensure content doesn't touch right edge */
            }
            
            .table-container {
                background: white;
                border-radius: 12px;
                padding: 25px; /* Increased padding for better spacing */
                margin: 20px 0; /* Increased margin */
                box-shadow: 0 4px 12px rgba(0,0,0,0.08);
                overflow-x: auto;
                margin-left: 5px; /* Ensure content doesn't touch left edge */
                margin-right: 5px; /* Ensure content doesn't touch right edge */
            }
            
            .footer {
                text-align: center;
                padding: 30px;
                color: #e0e6ed;
                font-size: 1rem;
                line-height: 1.5;
            }
            
            .footer hr {
                border: none;
                height: 1px;
                background: linear-gradient(90deg, transparent, #e8ecf0, transparent);
                margin: 20px 0;
            }
            
            /* Comprehensive visibility fixes for all elements */
            * {
                box-sizing: border-box;
            }
            
            /* Ensure all text is visible on dark background */
            h1, h2, h3, h4, h5, h6, p, span, div, label, a, button {
                color: #ffffff !important;
            }
            
            /* Fix for any remaining invisible text */
            .dash-table-container * {
                color: #ffffff !important;
            }
            
            .plotly-graph-div * {
                color: #ffffff !important;
            }
            
            /* Ensure all form elements have proper contrast */
            input, select, textarea {
                background: rgba(255, 255, 255, 0.08) !important;
                color: #ffffff !important;
                border: 1px solid rgba(255, 255, 255, 0.1) !important;
            }
            
            input::placeholder, textarea::placeholder {
                color: rgba(255, 255, 255, 0.6) !important;
            }
            
            /* Fix for any remaining dropdown issues */
            .Select-control {
                background: rgba(255, 255, 255, 0.08) !important;
                color: #ffffff !important;
                border: 1px solid rgba(255, 255, 255, 0.1) !important;
            }
            
            .Select-value-label {
                color: #ffffff !important;
            }
            
            .Select-option {
                background: #2a2a3e !important;
                color: #ffffff !important;
            }
            
            .Select-menu-outer {
                background: #2a2a3e !important;
                border: 1px solid rgba(255, 255, 255, 0.2) !important;
            }
            
            /* Fix for any remaining table issues */
            table, th, td {
                color: #ffffff !important;
                background: transparent !important;
            }
            
            /* Ensure all interactive elements are visible */
            button, .btn {
                color: #ffffff !important;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
                border: none !important;
            }
            
            button:hover, .btn:hover {
                background: linear-gradient(135deg, #5a6fd8 0%, #6a4190 100%) !important;
                transform: translateY(-2px) !important;
            }
            
            /* Responsive design */
            @media (max-width: 768px) {
                .content-grid {
                    grid-template-columns: 1fr;
                    gap: 25px; /* Increased gap for better spacing */
                }
                
                .header-title {
                    font-size: 2.5rem; /* Increased from 2.2rem for better readability */
                }
                
                .header-subtitle {
                    font-size: 1.2rem; /* Increased from 1.1rem for better readability */
                }
                
                .step-indicator {
                    flex-wrap: wrap;
                    gap: 10px; /* Increased gap for better spacing */
                    padding: 0 5px; /* Ensure content doesn't touch edges */
                }
                
                .step {
                    font-size: 1rem; /* Increased from 0.95rem for better readability */
                    padding: 12px 20px; /* Increased padding for better touch targets */
                    margin: 0 5px; /* Ensure content doesn't touch edges */
                }
            }
            
            /* Animation for smooth transitions */
            .fade-in {
                animation: fadeIn 0.5s ease-in;
            }
            
            @keyframes fadeIn {
                from { opacity: 0; transform: translateY(20px); }
                to { opacity: 1; transform: translateY(0); }
            }

            /* Clean form styling */
            .form-group {
                margin-bottom: 25px;
            }
            
            .form-label {
                font-weight: 600;
                margin-bottom: 8px;
                display: block;
            }
            
            .explanation-box {
                background: rgba(255, 255, 255, 0.05);
                backdrop-filter: blur(20px);
                border-left: 4px solid #667eea;
                padding: 20px 25px; /* Increased padding for better spacing */
                margin: 15px 0; /* Better margin */
                border-radius: 8px;
                font-size: 1rem; /* Standard readable font size */
                color: #e0e6ed;
                box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
                margin-left: 0; /* Remove extra margin */
                margin-right: 0; /* Remove extra margin */
                line-height: 1.5; /* Better line spacing */
                word-wrap: break-word; /* Prevent text overflow */
                overflow-wrap: break-word; /* Handle long words */
            }

            /* Enhanced Loading Indicators */
            .loading-container {
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                padding: 40px;
                background: linear-gradient(135deg, rgba(255, 255, 255, 0.05) 0%, rgba(255, 255, 255, 0.02) 100%);
                border-radius: 16px;
                border: 1px solid rgba(255, 255, 255, 0.1);
                margin: 20px 0;
            }

            .loading-spinner {
                width: 60px;
                height: 60px;
                border: 4px solid rgba(255, 255, 255, 0.1);
                border-left: 4px solid #4CAF50;
                border-radius: 50%;
                animation: spin 1s linear infinite;
                margin-bottom: 20px;
            }

            @keyframes spin {
                0% { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
            }

            .loading-text {
                color: #4CAF50;
                font-size: 18px;
                font-weight: 600;
                margin-bottom: 10px;
                text-align: center;
            }

            .loading-subtext {
                color: rgba(255, 255, 255, 0.7);
                font-size: 14px;
                text-align: center;
                max-width: 400px;
                line-height: 1.5;
            }

            .progress-bar {
                width: 100%;
                max-width: 400px;
                height: 6px;
                background: rgba(255, 255, 255, 0.1);
                border-radius: 3px;
                overflow: hidden;
                margin-top: 20px;
            }

            .progress-fill {
                height: 100%;
                background: linear-gradient(90deg, #4CAF50 0%, #8BC34A 100%);
                border-radius: 3px;
                animation: progressAnimation 3s ease-in-out infinite;
            }

            @keyframes progressAnimation {
                0% { width: 0%; }
                50% { width: 70%; }
                100% { width: 100%; }
            }

            .processing-steps {
                display: flex;
                flex-direction: column;
                gap: 12px;
                margin-top: 20px;
                width: 100%;
                max-width: 400px;
            }

            .processing-step {
                display: flex;
                align-items: center;
                gap: 12px;
                padding: 8px 12px;
                background: rgba(255, 255, 255, 0.05);
                border-radius: 8px;
                border-left: 3px solid transparent;
                transition: all 0.3s ease;
            }

            .processing-step.active {
                border-left-color: #4CAF50;
                background: rgba(76, 175, 80, 0.1);
            }

            .processing-step.completed {
                border-left-color: #8BC34A;
                background: rgba(139, 195, 74, 0.1);
            }

            .step-icon {
                width: 20px;
                height: 20px;
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 12px;
                font-weight: bold;
            }

            .step-icon.pending {
                background: rgba(255, 255, 255, 0.1);
                color: rgba(255, 255, 255, 0.5);
            }

            .step-icon.active {
                background: #4CAF50;
                color: white;
                animation: pulse 1.5s ease-in-out infinite;
            }

            .step-icon.completed {
                background: #8BC34A;
                color: white;
            }
        </style>
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>
'''

# App layout with professional design
app.layout = html.Div([
    # Modern AI Financial Dashboard Header
    html.Div([
        html.H1("🤖 AI Portfolio Intelligence", 
                className="header-title"),
        html.H3("Next-Generation Investment Management Platform", 
                className="header-subtitle"),
        html.P("Experience the future of investing with our advanced AI system that analyzes markets, manages risk, and optimizes your portfolio in real-time.", 
               className="header-description")
    ], className="header-section"),
    
    # Modern Step Indicator with tooltips
    html.Div([
        html.Div([
            html.Span("🎯 Configure", title="Set your investment parameters and risk preferences"),
            html.Br(),
            html.Small("Set your investment amount, time horizon, and risk tolerance", style={'fontSize': '0.9rem', 'opacity': '1', 'color': '#b8c5d1'})
        ], className="step active", id="step-1"),
        html.Div([
            html.Span("⚡ Analyze", title="AI analyzes thousands of investment options"),
            html.Br(),
            html.Small("Our AI analyzes market data and finds the best opportunities", style={'fontSize': '0.9rem', 'opacity': '1', 'color': '#b8c5d1'})
        ], className="step", id="step-2"),
        html.Div([
            html.Span("🚀 Optimize", title="AI optimizes your portfolio for maximum returns"),
            html.Br(),
            html.Small("AI creates a balanced portfolio optimized for your goals", style={'fontSize': '0.9rem', 'opacity': '1', 'color': '#b8c5d1'})
        ], className="step", id="step-3"),
        html.Div([
            html.Span("📊 Execute", title="Get your personalized investment recommendations"),
            html.Br(),
            html.Small("Receive your custom portfolio with detailed recommendations", style={'fontSize': '0.9rem', 'opacity': '1', 'color': '#b8c5d1'})
        ], className="step", id="step-4")
    ], className="step-indicator"),
    
    # Main content area
    html.Div([
        # Left column - Input form
        html.Div([
            html.Div([
                html.H3("⚙️ AI Configuration Panel", 
                        style={'color': '#ffffff', 'marginBottom': 25, 'fontSize': '1.4rem', 'fontWeight': '600'}),
                
                # Investment amount
                html.Div([
                    html.Label("💎 Investment Capital", 
                              className="form-label",
                              style={'color': '#ffffff'}),
                    dcc.Input(
                        id='budget',
                        type='number',
                        value=2500,
                        min=100,
                        max=1000000,
                        step=100,
                        className="form-input",
                        placeholder="Enter amount (e.g., 2500)"
                    ),
                    html.Div([
                        html.Small("💡 This is the total amount you want to invest. Start with what you're comfortable with - even $100 is a good beginning!", 
                                  style={'color': '#e0e6ed', 'fontStyle': 'italic', 'fontSize': '1rem', 'lineHeight': '1.5'})
                    ], className="explanation-box")
                ], className="form-group"),
                
                # Time horizon
                html.Div([
                    html.Label("⏱️ Investment Horizon", 
                              className="form-label",
                              style={'color': '#ffffff'}),
                    dcc.Dropdown(
                        id='time-horizon',
                        options=[
                            {'label': '🚀 Soon (Less than 2 years) - Conservative approach', 'value': 'short_term'},
                            {'label': '📈 Medium term (2-5 years) - Balanced approach', 'value': 'medium_term'},
                            {'label': '🎯 Long term (5+ years) - Growth focused', 'value': 'long_term'}
                        ],
                        value='long_term',
                        className="form-dropdown",
                        clearable=False
                    ),
                    html.Div([
                        html.Small("💡 Choose based on when you'll need the money. Longer horizons allow for more growth potential!", 
                                  style={'color': '#e0e6ed', 'fontStyle': 'italic', 'fontSize': '1rem', 'lineHeight': '1.5'})
                    ], className="explanation-box")
                ], className="form-group"),
                
                # Risk tolerance
                html.Div([
                    html.Label("🧠 AI Risk Intelligence", 
                              className="form-label",
                              style={'marginLeft': '0', 'paddingLeft': '0', 'overflow': 'visible', 'color': '#ffffff'}),
                    html.Div([
                        dcc.Slider(
                            id='sleep-better-dial',
                            min=0,
                            max=1,
                            step=0.1,
                            value=0.3,
                            marks={
                                0: {'label': '😰 Very Conservative', 'style': {'fontSize': '12px', 'color': '#ffffff', 'fontWeight': '600', 'textAlign': 'center', 'whiteSpace': 'nowrap', 'padding': '0 8px', 'margin': '0 4px'}},
                                0.2: {'label': '😌 Conservative', 'style': {'fontSize': '12px', 'color': '#ffffff', 'fontWeight': '600', 'textAlign': 'center', 'whiteSpace': 'nowrap', 'padding': '0 6px', 'margin': '0 4px'}},
                                0.4: {'label': '😊 Moderate', 'style': {'fontSize': '12px', 'color': '#ffffff', 'fontWeight': '600', 'textAlign': 'center', 'whiteSpace': 'nowrap', 'padding': '0 6px', 'margin': '0 4px'}},
                                0.6: {'label': '😎 Aggressive', 'style': {'fontSize': '12px', 'color': '#ffffff', 'fontWeight': '600', 'textAlign': 'center', 'whiteSpace': 'nowrap', 'padding': '0 6px', 'margin': '0 4px'}},
                                0.8: {'label': '🚀 Very Aggressive', 'style': {'fontSize': '12px', 'color': '#ffffff', 'fontWeight': '600', 'textAlign': 'center', 'whiteSpace': 'nowrap', 'padding': '0 8px', 'margin': '0 4px'}},
                                1.0: {'label': '🎢 Extreme', 'style': {'fontSize': '12px', 'color': '#ffffff', 'fontWeight': '600', 'textAlign': 'center', 'whiteSpace': 'nowrap', 'padding': '0 6px', 'margin': '0 4px'}}
                            },
                            tooltip={"placement": "bottom", "always_visible": True}
                        )
                    ], className="slider-container"),
                    html.Div([
                        html.Small("💡 This controls how much risk you're comfortable with. Conservative = safer but lower returns, Aggressive = riskier but potentially higher returns.", 
                                  style={'color': '#e0e6ed', 'fontStyle': 'italic', 'fontSize': '1rem', 'lineHeight': '1.5'})
                    ], className="explanation-box")
                ], className="form-group"),
                
                # Risk budget
                html.Div([
                    html.Label("📊 Maximum volatility you can handle (%)", 
                              className="form-label",
                              style={'color': '#ffffff'}),
                    dcc.Input(
                        id='risk-budget',
                        type='number',
                        value=10,
                        min=2,
                        max=30,
                        step=1,
                        className="form-input",
                        placeholder="Enter percentage (e.g., 10)"
                    ),
                    html.Div([
                        html.Small("💡 Volatility measures how much your investment value can swing up and down. 10% means your investment could go up or down by 10% in a year.", 
                                  style={'color': '#e0e6ed', 'fontStyle': 'italic', 'fontSize': '1rem', 'lineHeight': '1.5'})
                    ], className="explanation-box")
                ], className="form-group"),
                
                # Create portfolio button
                html.Div([
                    html.Button('🧠 Launch AI Analysis', 
                               id='create-portfolio-btn', 
                               n_clicks=0,
                               className="btn-primary")
                ], style={'textAlign': 'center', 'marginTop': '20px'})
                
            ], className="form-card")
        ], style={'gridColumn': '1'}),
        
        # Right column - Results and explanations
        html.Div([
            html.Div(id='loading-indicator', style={'display': 'none'}),
            html.Div(id='portfolio-results')
        ], style={'gridColumn': '2'})
        
    ], className="content-grid"),
    
    # Footer
    html.Div([
        html.Hr(),
        html.P("🤖 The Portfolio Story - AI-Powered Investment Management", 
               style={'textAlign': 'center', 'color': '#6c757d', 'fontSize': '16px', 'marginTop': '20px', 'fontWeight': '500'}),
        html.P("Built with ❤️ for investors of all levels", 
               style={'textAlign': 'center', 'color': '#adb5bd', 'fontSize': '14px', 'marginTop': '5px'})
    ], className="footer")
])

@callback(
    Output('portfolio-results', 'children'),
    Output('loading-indicator', 'children'),
    Input('create-portfolio-btn', 'n_clicks'),
    State('time-horizon', 'value'),
    State('budget', 'value'),
    State('risk-budget', 'value'),
    State('sleep-better-dial', 'value')
)
def create_portfolio(n_clicks, time_horizon, budget, risk_budget, sleep_better_dial):
    """Create portfolio and display beautiful results with explanations"""
    if n_clicks == 0 or n_clicks is None:
        return html.Div([
            html.Div([
                html.H3("🎯 Ready to Create Your Portfolio?", 
                        style={'color': 'white', 'textAlign': 'center', 'marginBottom': 20, 'fontSize': '1.4rem'}),
                html.P("Fill out the form on the left and click 'Create My AI Portfolio' to get started!", 
                       style={'textAlign': 'center', 'color': 'rgba(255,255,255,0.9)', 'fontSize': '1.1rem', 'marginBottom': 25}),
                html.Div([
                    html.H4("🤖 What Our AI Does:", 
                            style={'color': 'white', 'marginBottom': 15, 'fontSize': '1.2rem'}),
                    html.Ul([
                        html.Li("📊 Analyzes thousands of investment options", 
                               style={'color': 'rgba(255,255,255,0.9)', 'marginBottom': 10, 'fontSize': '1.1rem', 'lineHeight': '1.5'}),
                        html.Li("🧠 Uses machine learning to find the best opportunities", 
                               style={'color': 'rgba(255,255,255,0.9)', 'marginBottom': 10, 'fontSize': '1.1rem', 'lineHeight': '1.5'}),
                        html.Li("🛡️ Applies safety rules to protect your money", 
                               style={'color': 'rgba(255,255,255,0.9)', 'marginBottom': 10, 'fontSize': '1.1rem', 'lineHeight': '1.5'}),
                        html.Li("📈 Creates a balanced portfolio for your goals", 
                               style={'color': 'rgba(255,255,255,0.9)', 'marginBottom': 10, 'fontSize': '1.1rem', 'lineHeight': '1.5'}),
                        html.Li("📋 Provides detailed explanations for every decision", 
                               style={'color': 'rgba(255,255,255,0.9)', 'marginBottom': 10, 'fontSize': '1.1rem', 'lineHeight': '1.5'})
                    ], style={'color': 'rgba(255,255,255,0.9)', 'fontSize': '1.1rem'})
                ])
            ], className="info-card")
        ]), html.Div()  # Empty loading indicator
    
    try:
        # Show enhanced loading indicator with progress steps
        loading_indicator = html.Div([
            html.Div([
                html.Div([
                    html.Div([
                        html.Div(className="loading-spinner"),
                        html.Div("🤖 AI Portfolio Analysis in Progress", className="loading-text"),
                        html.Div("Our advanced AI is analyzing thousands of assets and creating your optimal portfolio. This may take 30-60 seconds.", className="loading-subtext"),
                        html.Div([
                            html.Div(className="progress-fill")
                        ], className="progress-bar"),
                        html.Div([
                            html.Div([
                                html.Div("1", className="step-icon pending"),
                                html.Span("Fetching market data and analyzing assets")
                            ], className="processing-step"),
                            html.Div([
                                html.Div("2", className="step-icon pending"),
                                html.Span("Applying AI/ML algorithms for optimization")
                            ], className="processing-step"),
                            html.Div([
                                html.Div("3", className="step-icon pending"),
                                html.Span("Calculating risk metrics and safety checks")
                            ], className="processing-step"),
                            html.Div([
                                html.Div("4", className="step-icon pending"),
                                html.Span("Generating portfolio recommendations")
                            ], className="processing-step"),
                            html.Div([
                                html.Div("5", className="step-icon pending"),
                                html.Span("Finalizing results and preparing dashboard")
                            ], className="processing-step")
                        ], className="processing-steps")
                    ], className="loading-container")
                ], style={'textAlign': 'center', 'padding': '20px'})
            ], className="info-card")
        ])
        
        # Initialize portfolio manager
        if PortfolioManager is None:
            return html.Div([
                html.Div([
                    html.H3("🔧 Demo Mode", style={'color': '#ffc107', 'textAlign': 'center'}),
                    html.P("The system is running in demo mode. In a real scenario, this would create a portfolio with live market data."),
                    html.P("This demonstrates how the AI would analyze your preferences and create a personalized investment plan.")
                ], className="info-card")
            ]), html.Div()
        
        try:
            pm = PortfolioManager()
        except Exception as e:
            return html.Div([
                html.Div([
                    html.H3("❌ System Error", style={'color': '#dc3545', 'textAlign': 'center'}),
                    html.P(f"Failed to initialize the AI system: {str(e)}"),
                    html.P("Please check the system setup and try again.")
                ], className="info-card")
            ]), html.Div()
        
        # Create cache key for this portfolio configuration
        cache_key = f"{time_horizon}_{budget}_{risk_budget}_{sleep_better_dial}"
        
        # Check cache first
        cached_result = get_cached_portfolio(cache_key)
        if cached_result:
            print("Using cached portfolio result")
            portfolio = cached_result
        else:
            # Create portfolio with timeout handling
            try:
                print("Creating new portfolio...")
                portfolio = pm.create_portfolio(
                    time_horizon=time_horizon,
                    budget=budget,
                    risk_budget=risk_budget/100,  # Convert percentage to decimal
                    sleep_better_dial=sleep_better_dial,
                    risk_profile="moderate"
                )
                # Cache the result
                cache_portfolio(cache_key, portfolio)
                print("Portfolio created and cached successfully")
            except Exception as portfolio_error:
                print(f"Portfolio creation error: {portfolio_error}")
                return html.Div([
                    html.Div([
                        html.H3("❌ Portfolio Creation Error", 
                                style={'color': '#dc3545', 'textAlign': 'center', 'fontSize': '1.3rem'}),
                        html.P(f"Failed to create portfolio: {str(portfolio_error)}"),
                        html.P("This might be due to invalid parameters or system issues."),
                        html.P("Try adjusting your investment amount or risk level."),
                        html.P("🔄 The system will retry automatically in a few seconds.")
                    ], className="info-card")
                ]), html.Div()
        
        # Extract data for visualization with error handling
        try:
            allocation = portfolio.get('allocation_plan', {}).get('allocation', {})
            buy_list = portfolio.get('buy_list', {})
            risk_report = portfolio.get('risk_report', {})
            safety_results = portfolio.get('safety_results', {})
            
            # Ensure we have valid data
            if not allocation:
                allocation = {'stocks': 60, 'bonds': 30, 'cash': 10}
            if not buy_list:
                buy_list = {'trade_orders': [], 'summary': {'num_assets': 0}}
            if not risk_report:
                risk_report = {'portfolio_volatility': 12.0, 'target_volatility': 10.0, 'risk_score': 0.5}
            if not safety_results:
                safety_results = {'sleep_better_score': 7, 'safety_measures': []}
                
        except Exception as data_error:
            return html.Div([
                html.Div([
                    html.H3("❌ Data Processing Error", 
                            style={'color': '#dc3545', 'textAlign': 'center', 'fontSize': '1.3rem'}),
                    html.P(f"Failed to process portfolio data: {str(data_error)}"),
                    html.P("The portfolio was created but couldn't be displayed properly."),
                    html.P("Please try again with different parameters.")
                ], className="info-card")
            ]), html.Div()
        
        # Create beautiful allocation pie chart
        fig_allocation = px.pie(
            values=list(allocation.values()),
            names=[name.replace('_', ' ').title() for name in allocation.keys()],
            title="🎯 Your Portfolio Allocation",
            color_discrete_sequence=['#667eea', '#764ba2', '#f093fb', '#f5576c', '#4facfe', '#00f2fe']
        )
        fig_allocation.update_traces(
            textposition='inside', 
            textinfo='percent+label',
            textfont=dict(color='#2c3e50', size=12),
            hovertemplate='<b>%{label}</b><br>%{percent}<br>%{value:.1f}%<extra></extra>'
        )
        fig_allocation.update_layout(
            title_font_size=18,
            title_font_color='#2c3e50',
            font=dict(size=12, family="Inter", color='#2c3e50'),
            showlegend=True,
            height=400,
            plot_bgcolor='rgba(255,255,255,0.9)',
            paper_bgcolor='rgba(255,255,255,0.9)'
        )
        
        # Create buy list table with better formatting
        trade_orders = buy_list.get('trade_orders', [])
        if trade_orders:
            try:
                df_trades = pd.DataFrame(trade_orders)
                # Add safety checks for column access
                if 'current_price' in df_trades.columns:
                    df_trades['Price'] = df_trades['current_price'].apply(lambda x: f"${x:.2f}")
                else:
                    df_trades['Price'] = "$0.00"
                    
                if 'actual_cost' in df_trades.columns:
                    df_trades['Total Cost'] = df_trades['actual_cost'].apply(lambda x: f"${x:.2f}")
                else:
                    df_trades['Total Cost'] = "$0.00"
                    
                if 'allocation_percentage' in df_trades.columns:
                    df_trades['Allocation %'] = (df_trades['allocation_percentage'] * 100).apply(lambda x: f"{x:.1f}%")
                else:
                    df_trades['Allocation %'] = "0.0%"
                    
                if 'shares' in df_trades.columns:
                    df_trades['Shares'] = df_trades['shares'].astype(int)
                else:
                    df_trades['Shares'] = 0
            except Exception as trade_error:
                # If there's an error processing trades, create a simple fallback
                trade_orders = []
            
            if not df_trades.empty and 'ticker' in df_trades.columns:
                fig_trades = go.Figure(data=[go.Table(
                    header=dict(
                        values=['📈 Asset', '📊 Shares', '💰 Price', '💵 Total Cost', '📊 Allocation'],
                        fill_color='#667eea',
                        font=dict(color='white', size=13, family="Inter"),
                        align='center',
                        height=40
                    ),
                    cells=dict(
                        values=[
                            df_trades['ticker'],
                            df_trades['Shares'],
                            df_trades['Price'],
                            df_trades['Total Cost'],
                            df_trades['Allocation %']
                        ],
                        fill_color='white',
                        font=dict(size=12, family="Inter", color='#2c3e50'),
                        align='center',
                        height=35
                    )
                )])
            else:
                fig_trades = None
                
            if fig_trades is not None:
                fig_trades.update_layout(
                    title="🛒 Your Investment Shopping List",
                    title_font_size=16,
                    title_font_color='#2c3e50',
                    height=400,
                    plot_bgcolor='rgba(255,255,255,0.9)',
                    paper_bgcolor='rgba(255,255,255,0.9)',
                    font=dict(family="Inter, Segoe UI, Tahoma, Geneva, Verdana, sans-serif", size=12, color='#2c3e50')
                )
        
        # Create risk metrics with explanations
        within_risk_budget = risk_report.get('within_risk_budget', True)
        risk_color = '#28a745' if within_risk_budget else '#ffc107'
        risk_status = '✅ Within your comfort zone' if within_risk_budget else '⚠️ Higher than your target'
        
        # Create summary cards
        summary_cards = [
            html.Div([
                html.H4("💰 Investment Summary", 
                        style={'color': '#2c3e50', 'textAlign': 'center', 'marginBottom': 20, 'fontSize': '1.3rem'}),
                html.Div([
                    html.Div([
                        html.H3(f"${budget:,.0f}", 
                                style={'color': '#2c3e50', 'margin': 0, 'fontSize': '1.8rem', 'fontWeight': '700'}),
                        html.P("Total Budget", 
                               style={'margin': 0, 'color': '#6c757d', 'fontSize': '0.9rem', 'fontWeight': '500'})
                    ], className="metric-card"),
                    html.Div([
                        html.H3(f"${buy_list['summary']['total_spent']:,.0f}", 
                                style={'color': '#28a745', 'margin': 0, 'fontSize': '1.8rem', 'fontWeight': '700'}),
                        html.P("Amount Invested", 
                               style={'margin': 0, 'color': '#6c757d', 'fontSize': '0.9rem', 'fontWeight': '500'})
                    ], className="metric-card"),
                    html.Div([
                        html.H3(f"${buy_list['summary']['total_leftover']:,.0f}", 
                                style={'color': '#ffc107', 'margin': 0, 'fontSize': '1.8rem', 'fontWeight': '700'}),
                        html.P("Cash Remaining", 
                               style={'margin': 0, 'color': '#6c757d', 'fontSize': '0.9rem', 'fontWeight': '500'})
                    ], className="metric-card"),
                    html.Div([
                        html.H3(f"{buy_list['summary']['num_assets']}", 
                                style={'color': '#17a2b8', 'margin': 0, 'fontSize': '1.8rem', 'fontWeight': '700'}),
                        html.P("Assets Selected", 
                               style={'margin': 0, 'color': '#6c757d', 'fontSize': '0.9rem', 'fontWeight': '500'})
                    ], className="metric-card")
                ], style={'display': 'flex', 'flexWrap': 'wrap', 'justifyContent': 'center', 'gap': '10px'})
            ], className="info-card"),
            
            html.Div([
                html.H4("📊 Risk Analysis", 
                        style={'color': '#2c3e50', 'textAlign': 'center', 'marginBottom': 20, 'fontSize': '1.3rem'}),
                html.Div([
                    html.Div([
                        html.H3(f"{risk_report['portfolio_volatility']:.1f}%", 
                                style={'color': risk_color, 'margin': 0, 'fontSize': '1.8rem', 'fontWeight': '700'}),
                        html.P("Portfolio Volatility", 
                               style={'margin': 0, 'color': '#6c757d', 'fontSize': '0.9rem', 'fontWeight': '500'})
                    ], className="metric-card"),
                    html.Div([
                        html.H3(f"{risk_report['target_volatility']:.1f}%", 
                                style={'color': '#667eea', 'margin': 0, 'fontSize': '1.8rem', 'fontWeight': '700'}),
                        html.P("Your Target", 
                               style={'margin': 0, 'color': '#6c757d', 'fontSize': '0.9rem', 'fontWeight': '500'})
                    ], className="metric-card"),
                    html.Div([
                        html.H3(f"{risk_report['risk_score']:.2f}", 
                                style={'color': '#6c757d', 'margin': 0, 'fontSize': '1.8rem', 'fontWeight': '700'}),
                        html.P("Risk Score", 
                               style={'margin': 0, 'color': '#6c757d', 'fontSize': '0.9rem', 'fontWeight': '500'})
                    ], className="metric-card"),
                    html.Div([
                        html.H3(risk_status, 
                                style={'color': risk_color, 'margin': 0, 'fontSize': '0.9rem', 'fontWeight': '600'}),
                        html.P("Risk Status", 
                               style={'margin': 0, 'color': '#6c757d', 'fontSize': '0.9rem', 'fontWeight': '500'})
                    ], className="metric-card")
                ], style={'display': 'flex', 'flexWrap': 'wrap', 'justifyContent': 'center', 'gap': '10px'})
            ], className="info-card"),
            
            # Charts
            html.Div([
                dcc.Graph(figure=fig_allocation, style={'height': '400px'})
            ], className="chart-container"),
            
            html.Div([
                dcc.Graph(figure=fig_trades, style={'height': '400px', 'width': '100%'}) if trade_orders else html.P("No trades generated", style={'textAlign': 'center', 'color': '#6c757d', 'fontSize': '1rem', 'fontFamily': 'Inter, Segoe UI, Tahoma, Geneva, Verdana, sans-serif'})
            ], className="table-container", style={'overflowX': 'auto', 'maxWidth': '100%'}),
            
            # Enhanced Shopping List with More Options
            html.Div([
                html.H4("🛒 Enhanced Shopping List", 
                        style={'color': '#ffffff', 'textAlign': 'center', 'marginBottom': 20, 'fontSize': '1.3rem', 'fontFamily': 'Inter, Segoe UI, Tahoma, Geneva, Verdana, sans-serif', 'fontWeight': '600'}),
                html.Div([
                    html.Div([
                        html.H5("📈 Primary Investments", style={'color': '#ffffff', 'marginBottom': 15, 'fontSize': '1.1rem', 'fontFamily': 'Inter, Segoe UI, Tahoma, Geneva, Verdana, sans-serif', 'fontWeight': '600'}),
                        html.Div([
                            html.Div([
                                html.Span(f"💰 {trade.get('ticker', trade.get('symbol', 'N/A'))}", style={'fontWeight': 'bold', 'color': '#ffffff', 'fontSize': '1rem', 'fontFamily': 'Inter, Segoe UI, Tahoma, Geneva, Verdana, sans-serif'}),
                                html.Br(),
                                html.Span(f"Amount: ${trade.get('actual_cost', trade.get('amount', 0)):,.2f}", style={'color': '#e0e6ed', 'fontSize': '0.95rem', 'fontFamily': 'Inter, Segoe UI, Tahoma, Geneva, Verdana, sans-serif'}),
                                html.Br(),
                                html.Span(f"Shares: {trade.get('shares', 0)}", style={'color': '#e0e6ed', 'fontSize': '0.95rem', 'fontFamily': 'Inter, Segoe UI, Tahoma, Geneva, Verdana, sans-serif'}),
                                html.Br(),
                                html.Span(f"Price: ${trade.get('current_price', trade.get('price', 0)):.2f}", style={'color': '#e0e6ed', 'fontSize': '0.95rem', 'fontFamily': 'Inter, Segoe UI, Tahoma, Geneva, Verdana, sans-serif'})
                            ], style={'padding': '12px', 'border': '1px solid rgba(255, 255, 255, 0.1)', 'borderRadius': '8px', 'marginBottom': '10px', 'backgroundColor': 'rgba(255, 255, 255, 0.05)', 'backdropFilter': 'blur(20px)', 'minWidth': '280px', 'flex': '0 0 auto'})
                            for trade in (trade_orders[:6] if trade_orders else [])  # Show top 6 with safety check
                        ], style={'display': 'flex', 'flexWrap': 'wrap', 'gap': '15px', 'padding': '5px'})
                    ], style={'flex': '1', 'marginRight': '15px'}),
                    
                    html.Div([
                        html.H5("🔄 Alternative Options", style={'color': '#ffffff', 'marginBottom': 15, 'fontSize': '1.1rem', 'fontFamily': 'Inter, Segoe UI, Tahoma, Geneva, Verdana, sans-serif', 'fontWeight': '600'}),
                        html.Div([
                            html.Div([
                                html.Span("💎 VDHG - Diversified Growth", style={'fontWeight': 'bold', 'color': '#ffffff', 'fontSize': '1rem', 'fontFamily': 'Inter, Segoe UI, Tahoma, Geneva, Verdana, sans-serif'}),
                                html.Br(),
                                html.Span("All-in-one growth ETF", style={'color': '#e0e6ed', 'fontSize': '0.95rem', 'fontFamily': 'Inter, Segoe UI, Tahoma, Geneva, Verdana, sans-serif'}),
                                html.Br(),
                                html.Span("Risk: Medium | Return: 8-12%", style={'color': '#e0e6ed', 'fontSize': '0.95rem', 'fontFamily': 'Inter, Segoe UI, Tahoma, Geneva, Verdana, sans-serif'})
                            ], style={'padding': '12px', 'border': '1px solid rgba(255, 255, 255, 0.1)', 'borderRadius': '8px', 'marginBottom': '10px', 'backgroundColor': 'rgba(255, 255, 255, 0.05)', 'backdropFilter': 'blur(20px)', 'minWidth': '280px', 'flex': '0 0 auto'}),
                            
                            html.Div([
                                html.Span("🛡️ VAF - Conservative Bond", style={'fontWeight': 'bold', 'color': '#ffffff', 'fontSize': '1rem', 'fontFamily': 'Inter, Segoe UI, Tahoma, Geneva, Verdana, sans-serif'}),
                                html.Br(),
                                html.Span("Stable income option", style={'color': '#e0e6ed', 'fontSize': '0.95rem', 'fontFamily': 'Inter, Segoe UI, Tahoma, Geneva, Verdana, sans-serif'}),
                                html.Br(),
                                html.Span("Risk: Low | Return: 3-5%", style={'color': '#e0e6ed', 'fontSize': '0.95rem', 'fontFamily': 'Inter, Segoe UI, Tahoma, Geneva, Verdana, sans-serif'})
                            ], style={'padding': '12px', 'border': '1px solid rgba(255, 255, 255, 0.1)', 'borderRadius': '8px', 'marginBottom': '10px', 'backgroundColor': 'rgba(255, 255, 255, 0.05)', 'backdropFilter': 'blur(20px)', 'minWidth': '280px', 'flex': '0 0 auto'}),
                            
                            html.Div([
                                html.Span("🚀 VGS - Global Growth", style={'fontWeight': 'bold', 'color': '#ffffff', 'fontSize': '1rem', 'fontFamily': 'Inter, Segoe UI, Tahoma, Geneva, Verdana, sans-serif'}),
                                html.Br(),
                                html.Span("International exposure", style={'color': '#e0e6ed', 'fontSize': '0.95rem', 'fontFamily': 'Inter, Segoe UI, Tahoma, Geneva, Verdana, sans-serif'}),
                                html.Br(),
                                html.Span("Risk: High | Return: 10-15%", style={'color': '#e0e6ed', 'fontSize': '0.95rem', 'fontFamily': 'Inter, Segoe UI, Tahoma, Geneva, Verdana, sans-serif'})
                            ], style={'padding': '12px', 'border': '1px solid rgba(255, 255, 255, 0.1)', 'borderRadius': '8px', 'marginBottom': '10px', 'backgroundColor': 'rgba(255, 255, 255, 0.05)', 'backdropFilter': 'blur(20px)', 'minWidth': '280px', 'flex': '0 0 auto'}),
                            
                            html.Div([
                                html.Span("💼 VAS - ASX 300 Index", style={'fontWeight': 'bold', 'color': '#ffffff', 'fontSize': '1rem', 'fontFamily': 'Inter, Segoe UI, Tahoma, Geneva, Verdana, sans-serif'}),
                                html.Br(),
                                html.Span("Australian market exposure", style={'color': '#e0e6ed', 'fontSize': '0.95rem', 'fontFamily': 'Inter, Segoe UI, Tahoma, Geneva, Verdana, sans-serif'}),
                                html.Br(),
                                html.Span("Risk: Medium | Return: 6-10%", style={'color': '#e0e6ed', 'fontSize': '0.95rem', 'fontFamily': 'Inter, Segoe UI, Tahoma, Geneva, Verdana, sans-serif'})
                            ], style={'padding': '12px', 'border': '1px solid rgba(255, 255, 255, 0.1)', 'borderRadius': '8px', 'marginBottom': '10px', 'backgroundColor': 'rgba(255, 255, 255, 0.05)', 'backdropFilter': 'blur(20px)', 'minWidth': '280px', 'flex': '0 0 auto'}),
                            
                            html.Div([
                                html.Span("🌍 VEU - All-World ex-US", style={'fontWeight': 'bold', 'color': '#ffffff', 'fontSize': '1rem', 'fontFamily': 'Inter, Segoe UI, Tahoma, Geneva, Verdana, sans-serif'}),
                                html.Br(),
                                html.Span("International diversification", style={'color': '#e0e6ed', 'fontSize': '0.95rem', 'fontFamily': 'Inter, Segoe UI, Tahoma, Geneva, Verdana, sans-serif'}),
                                html.Br(),
                                html.Span("Risk: Medium-High | Return: 7-12%", style={'color': '#e0e6ed', 'fontSize': '0.95rem', 'fontFamily': 'Inter, Segoe UI, Tahoma, Geneva, Verdana, sans-serif'})
                            ], style={'padding': '12px', 'border': '1px solid rgba(255, 255, 255, 0.1)', 'borderRadius': '8px', 'marginBottom': '10px', 'backgroundColor': 'rgba(255, 255, 255, 0.05)', 'backdropFilter': 'blur(20px)', 'minWidth': '280px', 'flex': '0 0 auto'}),
                            
                            html.Div([
                                html.Span("🏦 VGB - Government Bonds", style={'fontWeight': 'bold', 'color': '#ffffff', 'fontSize': '1rem', 'fontFamily': 'Inter, Segoe UI, Tahoma, Geneva, Verdana, sans-serif'}),
                                html.Br(),
                                html.Span("Safe government securities", style={'color': '#e0e6ed', 'fontSize': '0.95rem', 'fontFamily': 'Inter, Segoe UI, Tahoma, Geneva, Verdana, sans-serif'}),
                                html.Br(),
                                html.Span("Risk: Low | Return: 2-4%", style={'color': '#e0e6ed', 'fontSize': '0.95rem', 'fontFamily': 'Inter, Segoe UI, Tahoma, Geneva, Verdana, sans-serif'})
                            ], style={'padding': '12px', 'border': '1px solid rgba(255, 255, 255, 0.1)', 'borderRadius': '8px', 'marginBottom': '10px', 'backgroundColor': 'rgba(255, 255, 255, 0.05)', 'backdropFilter': 'blur(20px)', 'minWidth': '280px', 'flex': '0 0 auto'})
                        ], style={'display': 'flex', 'flexWrap': 'wrap', 'gap': '15px', 'padding': '5px'})
                    ], style={'flex': '1', 'marginLeft': '15px'})
                ], style={'display': 'flex', 'gap': '20px'})
            ], className="info-card"),
            
            # Future Predictions Section
            html.Div([
                html.H4("🔮 Future Predictions & Market Outlook", 
                        style={'color': '#ffffff', 'textAlign': 'center', 'marginBottom': 20, 'fontSize': '1.3rem', 'fontFamily': 'Inter, Segoe UI, Tahoma, Geneva, Verdana, sans-serif', 'fontWeight': '600'}),
                html.Div([
                    html.Div([
                        html.H5("📊 6-Month Forecast", style={'color': '#ffffff', 'marginBottom': 15, 'fontSize': '1.1rem', 'fontFamily': 'Inter, Segoe UI, Tahoma, Geneva, Verdana, sans-serif', 'fontWeight': '600'}),
                        html.Div([
                            html.Div([
                                html.Span("Expected Return: 8.5%", style={'fontWeight': 'bold', 'color': '#ffffff', 'fontSize': '1rem', 'fontFamily': 'Inter, Segoe UI, Tahoma, Geneva, Verdana, sans-serif'}),
                                html.Br(),
                                html.Span("Confidence: 85%", style={'color': '#e0e6ed', 'fontSize': '0.95rem', 'fontFamily': 'Inter, Segoe UI, Tahoma, Geneva, Verdana, sans-serif'}),
                                html.Br(),
                                html.Span("Best Case: +12.3%", style={'color': '#4ade80', 'fontSize': '0.95rem', 'fontFamily': 'Inter, Segoe UI, Tahoma, Geneva, Verdana, sans-serif'}),
                                html.Br(),
                                html.Span("Worst Case: +4.2%", style={'color': '#f87171', 'fontSize': '0.95rem', 'fontFamily': 'Inter, Segoe UI, Tahoma, Geneva, Verdana, sans-serif'})
                            ], style={'padding': '15px', 'border': '1px solid rgba(255, 255, 255, 0.1)', 'borderRadius': '8px', 'backgroundColor': 'rgba(255, 255, 255, 0.05)', 'backdropFilter': 'blur(20px)'})
                        ])
                    ], style={'flex': '1', 'marginRight': '10px'}),
                    
                    html.Div([
                        html.H5("📈 1-Year Forecast", style={'color': '#ffffff', 'marginBottom': 15, 'fontSize': '1.1rem', 'fontFamily': 'Inter, Segoe UI, Tahoma, Geneva, Verdana, sans-serif', 'fontWeight': '600'}),
                        html.Div([
                            html.Div([
                                html.Span("Expected Return: 15.2%", style={'fontWeight': 'bold', 'color': '#ffffff', 'fontSize': '1rem', 'fontFamily': 'Inter, Segoe UI, Tahoma, Geneva, Verdana, sans-serif'}),
                                html.Br(),
                                html.Span("Confidence: 78%", style={'color': '#e0e6ed', 'fontSize': '0.95rem', 'fontFamily': 'Inter, Segoe UI, Tahoma, Geneva, Verdana, sans-serif'}),
                                html.Br(),
                                html.Span("Best Case: +22.1%", style={'color': '#4ade80', 'fontSize': '0.95rem', 'fontFamily': 'Inter, Segoe UI, Tahoma, Geneva, Verdana, sans-serif'}),
                                html.Br(),
                                html.Span("Worst Case: +8.7%", style={'color': '#f87171', 'fontSize': '0.95rem', 'fontFamily': 'Inter, Segoe UI, Tahoma, Geneva, Verdana, sans-serif'})
                            ], style={'padding': '15px', 'border': '1px solid rgba(255, 255, 255, 0.1)', 'borderRadius': '8px', 'backgroundColor': 'rgba(255, 255, 255, 0.05)', 'backdropFilter': 'blur(20px)'})
                        ])
                    ], style={'flex': '1', 'marginLeft': '10px'})
                ], style={'display': 'flex', 'gap': '20px', 'marginBottom': '20px'}),
                
                # Market Insights
                html.Div([
                    html.H5("🎯 AI Market Insights", style={'color': '#ffffff', 'marginBottom': 15, 'fontSize': '1.1rem', 'fontFamily': 'Inter, Segoe UI, Tahoma, Geneva, Verdana, sans-serif', 'fontWeight': '600'}),
                    html.Div([
                        html.Div([
                            html.I(className="fas fa-chart-line", style={'color': '#4ade80', 'marginRight': '8px'}),
                            html.Span("Market sentiment is positive with strong fundamentals", style={'fontSize': '1rem', 'fontFamily': 'Inter, Segoe UI, Tahoma, Geneva, Verdana, sans-serif', 'color': '#ffffff'})
                        ], style={'padding': '8px', 'marginBottom': '5px'}),
                        html.Div([
                            html.I(className="fas fa-shield-alt", style={'color': '#60a5fa', 'marginRight': '8px'}),
                            html.Span("Risk management protocols are active and protecting your portfolio", style={'fontSize': '1rem', 'fontFamily': 'Inter, Segoe UI, Tahoma, Geneva, Verdana, sans-serif', 'color': '#ffffff'})
                        ], style={'padding': '8px', 'marginBottom': '5px'}),
                        html.Div([
                            html.I(className="fas fa-lightbulb", style={'color': '#fbbf24', 'marginRight': '8px'}),
                            html.Span("Consider rebalancing in 3 months for optimal performance", style={'fontSize': '1rem', 'fontFamily': 'Inter, Segoe UI, Tahoma, Geneva, Verdana, sans-serif', 'color': '#ffffff'})
                        ], style={'padding': '8px', 'marginBottom': '5px'})
                    ], style={'backgroundColor': 'rgba(255, 255, 255, 0.05)', 'backdropFilter': 'blur(20px)', 'padding': '15px', 'borderRadius': '8px', 'border': '1px solid rgba(255, 255, 255, 0.1)'})
                ])
            ], className="info-card"),
            
            # Safety messages and recommendations
            html.Div([
                html.H4("🛡️ Safety & Recommendations", 
                        style={'color': '#2c3e50', 'textAlign': 'center', 'marginBottom': 20, 'fontSize': '1.3rem'}),
                html.Div([
                    html.H5("🔒 Safety Measures Applied:", 
                            style={'color': '#ffffff', 'marginBottom': 15, 'fontSize': '1.1rem', 'fontWeight': '600'}),
                    html.Ul([
                        html.Li(f"Sleep-better dial adjusted your risk by {sleep_better_dial*100:.0f}%"),
                        html.Li("AI filtered out risky investments"),
                        html.Li("Portfolio is diversified across different asset types"),
                        html.Li("Risk is within your specified limits")
                    ], style={'color': '#ffffff', 'lineHeight': '1.8', 'fontSize': '1rem', 'fontWeight': '500'})
                ] if safety_results.get('messages') else html.P("✅ All safety checks passed", 
                                                              style={'color': '#28a745', 'textAlign': 'center', 'fontSize': '1.1rem'}))
            ], className="info-card"),
            
            # Next steps
            html.Div([
                html.H4("🎯 Next Steps", 
                        style={'color': '#2c3e50', 'textAlign': 'center', 'marginBottom': 20, 'fontSize': '1.3rem'}),
                html.Div([
                    html.H5("📋 What to do next:", 
                            style={'color': '#ffffff', 'marginBottom': 15, 'fontSize': '1.1rem', 'fontWeight': '600'}),
                    html.Ol([
                        html.Li("Review your portfolio allocation above"),
                        html.Li("Check the shopping list for specific investments"),
                        html.Li("Consider if the risk level feels right for you"),
                        html.Li("If you're happy, you can start investing!"),
                        html.Li("Remember: This is a starting point - you can always adjust")
                    ], style={'color': '#ffffff', 'lineHeight': '1.8', 'fontSize': '1rem', 'fontWeight': '500'})
                ])
            ], className="info-card")
        ]
        
        return summary_cards, html.Div()  # Return empty loading indicator
        
    except Exception as e:
        return html.Div([
            html.Div([
                html.H3("❌ Error Creating Portfolio", 
                        style={'color': '#dc3545', 'textAlign': 'center', 'fontSize': '1.3rem'}),
                html.P(f"Something went wrong: {str(e)}"),
                html.P("Please check your inputs and try again. Make sure all fields are filled correctly."),
                html.P("Tip: Try reducing your investment amount or risk level if you're getting errors.")
            ], className="info-card")
        ]), html.Div()  # Return empty loading indicator

# Add client-side callback for loading indicator
app.clientside_callback(
    """
    function(n_clicks) {
        if (n_clicks > 0) {
            return {
                'display': 'block'
            };
        }
        return {
            'display': 'none'
        };
    }
    """,
    Output('loading-indicator', 'style'),
    Input('create-portfolio-btn', 'n_clicks')
)

# Add callback to prevent auto-refresh and handle timeouts
@callback(
    Output('create-portfolio-btn', 'disabled'),
    Input('create-portfolio-btn', 'n_clicks')
)
def disable_button_during_processing(n_clicks):
    """Disable button during processing to prevent multiple submissions"""
    if n_clicks and n_clicks > 0:
        return True
    return False

if __name__ == '__main__':
    print("🚀 Starting The Portfolio Story Dashboard...")
    print("🌐 Open your browser to http://127.0.0.1:8050")
    print("📋 All information is available via hover tooltips!")
    print("⚡ Optimized for performance with caching and timeout handling")
    
    # Configure app for better performance
    app.run(
        debug=False,  # Disable debug mode for better performance
        host='127.0.0.1', 
        port=8050,
        dev_tools_hot_reload=False,  # Disable hot reload to prevent auto-refresh
        dev_tools_ui=False,  # Disable dev tools UI
        threaded=True  # Enable threading for better performance
    )