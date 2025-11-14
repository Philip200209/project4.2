@app.route('/risk_analyst_dashboard')
@login_required
def risk_analyst_dashboard():
    """Enhanced Risk Analyst Dashboard with Advanced Analytics"""
    if current_user.role.lower() not in ['risk_analyst', 'admin']:
        flash('Access denied. Risk Analyst privileges required.', 'error')
        return redirect(url_for('dashboard'))
    
    try:
        print("DEBUG: Starting risk analyst dashboard...")
        
        # Portfolio Metrics
        total_loans = Loan.query.count()
        print(f"DEBUG: Total loans: {total_loans}")
        
        active_loans = Loan.query.filter(Loan.status.in_(['active', 'approved'])).count()
        print(f"DEBUG: Active loans: {active_loans}")
        
        # Calculate portfolio value
        portfolio_value_result = db.session.query(db.func.sum(Loan.amount)).filter(
            Loan.status.in_(['active', 'approved'])
        ).scalar()
        total_portfolio_value = portfolio_value_result or 0
        print(f"DEBUG: Portfolio value: {total_portfolio_value}")
        
        # Default rate
        defaulted_loans = Loan.query.filter_by(status='defaulted').count()
        print(f"DEBUG: Defaulted loans: {defaulted_loans}")
        
        default_rate = (defaulted_loans / active_loans * 100) if active_loans > 0 else 0
        
        # Portfolio Health Score
        performing_loans = active_loans - defaulted_loans
        portfolio_health = (performing_loans / active_loans * 100) if active_loans > 0 else 0
        
        # Risk Distribution
        risk_distribution = db.session.query(
            Loan.risk_level,
            db.func.count(Loan.id)
        ).filter(
            Loan.status.in_(['active', 'approved'])
        ).group_by(Loan.risk_level).all()
        
        # Convert to dictionary for easier template access
        risk_dist_dict = dict(risk_distribution) if risk_distribution else {}
        
        # High Risk Loans
        high_risk_loans = Loan.query.filter(
            Loan.status.in_(['active', 'approved']),
            Loan.risk_level == 'High'
        ).order_by(Loan.risk_score.asc()).limit(10).all()
        
        # Recent Interventions
        recent_interventions = Intervention.query.order_by(
            Intervention.sent_at.desc()
        ).limit(10).all()
        
        # Test helper functions one by one
        print("DEBUG: Testing monthly trends...")
        monthly_trends = get_portfolio_health_trends()
        print(f"DEBUG: Monthly trends: {monthly_trends}")
        
        print("DEBUG: Testing warning indicators...")
        warning_indicators = get_early_warning_indicators()
        print(f"DEBUG: Warning indicators: {warning_indicators}")
        
        print("DEBUG: Testing ML metrics...")
        model_metrics = get_ml_model_metrics()
        print(f"DEBUG: Model metrics: {model_metrics}")
        
        # Risk Alerts (sum of all warning indicators)
        risk_alerts = sum(warning_indicators.values())
        
        print("DEBUG: All data collected successfully, rendering template...")
        
        # ✅ CRITICAL: Return the template with all the data
        return render_template('risk_analyst_advanced.html',
                            total_loans=total_loans,
                            active_loans=active_loans,
                            total_portfolio_value=total_portfolio_value,
                            defaulted_loans=defaulted_loans,
                            default_rate=round(default_rate, 1),
                            portfolio_health=round(portfolio_health, 1),
                            risk_distribution=risk_dist_dict,
                            model_metrics=model_metrics,
                            high_risk_loans=high_risk_loans,
                            recent_interventions=recent_interventions,
                            monthly_trends=monthly_trends,
                            warning_indicators=warning_indicators,
                            risk_alerts=risk_alerts)
    
    except Exception as e:
        print(f"ERROR in risk analyst dashboard: {str(e)}")
        logger.error(f"Error in enhanced risk analyst dashboard: {e}")
        # Fallback to basic data
        return render_template('risk_analyst_advanced.html',
                            total_loans=0,
                            active_loans=0,
                            total_portfolio_value=0,
                            defaulted_loans=0,
                            default_rate=0,
                            portfolio_health=0,
                            risk_distribution={},
                            model_metrics={},
                            high_risk_loans=[],
                            recent_interventions=[],
                            monthly_trends=[],
                            warning_indicators={},
                            risk_alerts=0)