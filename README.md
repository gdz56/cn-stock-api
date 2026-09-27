# A股技术指标 API

基于新浪/腾讯免费行情数据，计算常用技术指标，供开发者调用。

## 部署
Vercel Serverless Functions (Python)

## 指标
- MA (均线)
- MACD
- RSI
- KDJ
- Bollinger Bands
- 成交量分析

## 端点
- `/api/quote?symbol=sh600519` — 实时行情
- `/api/kline?symbol=sh600519&period=day&count=120` — K线数据
- `/api/indicators?symbol=sh600519&period=day&types=ma,macd,rsi,kdj,boll&periods=5,10,20,60` — 技术指标
