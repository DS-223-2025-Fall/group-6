# DS 223 Marketing Analytics – Group Project Demo

## Product Overview
**Product Name:** EdRetain  
**Team Number:** Group Number 6   
**Demo Date:** December 11, 2025  

EdRetain is a smart churn prediction and predictive retention analytics system for premium users in EdTech platforms. It predicts which premium users are likely to downgrade or churn by analyzing engagement and spending patterns, enabling timely marketing interventions. The platform integrates data modeling, API access, and a user-friendly UI for actionable retention insights.

## Problem Definition
Subscription-based EdTech platforms face high churn rates among premium subscribers due to declining motivation, limited personalization, and free alternatives. The core issue is identifying at-risk premium users early through behavioral indicators like engagement and spending patterns. EdRetain provides churn-risk scores and segmentation to support personalized retention strategies, improving loyalty and revenue.

## Solution Architecture
**Product Roadmap:** [Product-Roadmap.pdf](Product Roadmap.png)  
**ERD (Entity Relationship Diagram):** [ERD.png](ERD.pdf)  
**UI Prototype** [UI Prototype.png](UI_Prototype.pdf)  
**Microservice Components:**  
  - **Frontend:** Streamlit – displays model outputs, visualizations, and churn dashboards.  
  - **Backend:** FastAPI – exposes endpoints for model predictions and database interactions.  
  - **Database:** PostgreSQL – stores user engagement, subscription, and prediction data.  
  - **Model:** Logistic Regression / XGBoost / K-Means Clustering – for churn prediction, RFM analysis, and segmentation.


## Team Roles
| Name | Role | Responsibility |
|------|------|----------------|
| Anzhela Davityan | Project/Product Manager | Planning, roadmap, team coordination |
| Arpine Janunts | Data Scientist | Data prep, modeling (RFM, clustering, churn prediction), evaluation |
| Melanie Melkonyan | Backend Developer | API with FastAPI |
| Amalya Tadevosyan | Database Developer | PostgreSQL setup, CRUD operations |
| Anna Mikayelyan | Frontend Developer | Streamlit app  |

## Live Demo Flow
1. **Introduction (by PM)**: Product overview, problem statement, MVP roadmap, architecture diagram.  
2. **Frontend (by PM)**: Streamlit UI navigation, churn visualizations, risk score interactions.  
3. **Backend (by PM)**: FastAPI endpoints via Swagger UI, data flow to model/database.  
4. **Model (by PM)**: Churn prediction type, metrics (retention rate, CLV), example outputs.  
5. **Database (by PM)**: Schema display (ERD), sample insert/query for premium user data.  
**Q&A Session**  

## Final Notes
All components are integrated and tested for the live demo. Complete final GitHub push by December 11, 2025, 23:59. Expected outcomes include reduced churn, higher CLV, and efficient campaigns. 
