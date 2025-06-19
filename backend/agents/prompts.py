"""
Prompts for Amazon Product Analysis System

This module contains all the prompts used by various analysis functions
in the Amazon product analysis system.
"""

def get_product_analysis_prompt(product_info: str) -> str:
    """
    Generate a comprehensive product analysis prompt.
    
    Args:
        product_info: Product information string to be analyzed
        
    Returns:
        Formatted prompt string for LLM analysis
    """
    return f"""
    You are an expert product analyst for Amazon marketplace. Analyze the following product information and provide a comprehensive status analysis.

    Product Information:
    {product_info}

    Please provide a detailed analysis covering the following aspects:

    1. MARKET POSITION ANALYSIS
    - Current pricing strategy and competitiveness
    - Brand positioning and market perception
    - Target customer segment identification

    2. PRODUCT PERFORMANCE METRICS
    - Customer satisfaction indicators (based on reviews)
    - Quality assessment from available data
    - Value proposition strength

    3. COMPETITIVE ADVANTAGES
    - Unique selling points
    - Differentiation factors
    - Market strengths

    4. AREAS FOR IMPROVEMENT
    - Potential weaknesses or gaps
    - Customer pain points (if evident from reviews)
    - Optimization opportunities

    5. MARKET TRENDS & OPPORTUNITIES
    - Current market positioning
    - Growth potential
    - Emerging trends alignment

    6. STRATEGIC RECOMMENDATIONS
    - Short-term tactical improvements
    - Long-term strategic positioning
    - Risk mitigation strategies

    Format your response as a comprehensive business analysis report. Be specific, actionable, and data-driven in your analysis. If certain information is missing, note what additional data would be valuable for a more complete analysis.
    """

def get_competitor_analysis_prompt(main_product_info: str, competitor_infos: tuple) -> str:
    """
    Generate a comprehensive competitor analysis prompt.
    
    Args:
        main_product_info: Main product information string to be analyzed
        competitor_infos: Tuple of competitor product information strings
        
    Returns:
        Formatted prompt string for LLM competitor analysis
    """
    competitors_section = "\n\n".join([f"COMPETITOR {i+1}:\n{info}" for i, info in enumerate(competitor_infos)])
    
    return f"""
    You are an expert competitive intelligence analyst for Amazon marketplace. Analyze the main product against its competitors and provide a comprehensive competitive analysis.

    MAIN PRODUCT:
    {main_product_info}

    COMPETITORS:
    {competitors_section}

    Please provide a detailed competitive analysis covering the following aspects:

    1. COMPETITIVE LANDSCAPE OVERVIEW
    - Market positioning of main product vs competitors
    - Competitive intensity and dynamics
    - Key players identification and market share insights

    2. PRICING ANALYSIS
    - Price positioning comparison across competitors
    - Value proposition assessment at different price points
    - Pricing strategy recommendations

    3. FEATURE & QUALITY COMPARISON
    - Feature-by-feature comparison matrix
    - Quality indicators (reviews, ratings, specifications)
    - Unique selling propositions of each competitor

    4. CUSTOMER PERCEPTION ANALYSIS
    - Review sentiment comparison
    - Customer satisfaction levels across products
    - Common complaints and praise points

    5. COMPETITIVE ADVANTAGES & GAPS
    - Main product's competitive strengths
    - Areas where competitors outperform
    - Market gaps and opportunities

    6. MARKET SHARE & PERFORMANCE INDICATORS
    - Sales performance indicators (if available)
    - Search ranking and visibility analysis
    - Brand strength assessment

    7. STRATEGIC RECOMMENDATIONS
    - Competitive positioning strategy
    - Areas for improvement to gain competitive edge
    - Defensive strategies against competitor threats
    - Offensive opportunities to capture market share

    8. THREAT ASSESSMENT
    - Immediate competitive threats
    - Emerging competitive risks
    - Market disruption potential

    Format your response as a comprehensive competitive intelligence report. Be specific, actionable, and strategic in your analysis. Provide clear recommendations for maintaining and improving competitive position. If certain competitive information is missing, note what additional competitor data would strengthen the analysis.
    """

def get_market_positioning_prompt(product_analysis_result: str, competitor_analysis_result: str) -> str:
    """
    Generate a comprehensive market positioning strategy prompt.
    
    Args:
        product_analysis_result: Product analysis results to base positioning on
        competitor_analysis_result: Competitor analysis results for context
        
    Returns:
        Formatted prompt string for LLM market positioning strategy
    """
    return f"""
    You are an expert marketing strategist specializing in Amazon marketplace positioning. Based on the product analysis and competitive intelligence provided, develop a comprehensive market positioning strategy.

    PRODUCT ANALYSIS:
    {product_analysis_result}

    COMPETITIVE ANALYSIS:
    {competitor_analysis_result}

    Please provide a detailed market positioning strategy covering the following aspects:

    1. POSITIONING STRATEGY FRAMEWORK
    - Core positioning statement and value proposition
    - Brand positioning relative to competitors
    - Unique market position identification

    2. TARGET CUSTOMER SEGMENTATION
    - Primary target customer profiles
    - Secondary target segments
    - Customer needs and pain points alignment
    - Demographic and psychographic characteristics

    3. COMPETITIVE DIFFERENTIATION
    - Key differentiators vs competitors
    - Competitive advantages to emphasize
    - Areas of parity to acknowledge
    - Strategies to overcome competitive disadvantages

    4. VALUE PROPOSITION DEVELOPMENT
    - Core value propositions for each target segment
    - Benefit hierarchy and prioritization
    - Emotional and rational benefits balance
    - Price-value equation optimization

    5. MESSAGING STRATEGY
    - Primary brand messaging pillars
    - Key communication themes
    - Tone and voice recommendations
    - Message architecture for different touchpoints

    6. CHANNEL POSITIONING STRATEGY
    - Amazon-specific positioning tactics
    - Category positioning within Amazon
    - Search and discovery optimization
    - Cross-platform consistency requirements

    7. PRICING POSITIONING
    - Price point strategy (premium, mid-tier, value)
    - Price anchoring and perception management
    - Promotional pricing strategies
    - Bundle and package positioning

    8. BRAND ARCHITECTURE
    - Brand hierarchy and relationships
    - Sub-brand or product line positioning
    - Brand extension opportunities
    - Portfolio positioning strategy

    9. IMPLEMENTATION ROADMAP
    - Phase 1: Immediate positioning actions (0-3 months)
    - Phase 2: Medium-term positioning development (3-12 months)
    - Phase 3: Long-term positioning evolution (12+ months)
    - Success metrics and KPIs

    10. RISK MITIGATION
    - Positioning risks and challenges
    - Competitive response scenarios
    - Market change adaptation strategies
    - Brand protection measures

    Format your response as a comprehensive marketing strategy document. Be specific, actionable, and strategically sound. Provide clear guidance that can be immediately implemented across Amazon marketplace optimization efforts. Include tactical recommendations alongside strategic direction.
    """

def get_product_optimizer_prompt(main_product_info: str, market_positioning_suggestions: str) -> str:
    """
    Generate a comprehensive product optimization strategy prompt.
    
    Args:
        main_product_info: Main product information to optimize
        market_positioning_suggestions: Market positioning strategy for context
        
    Returns:
        Formatted prompt string for LLM product optimization strategy
    """
    return f"""
    You are an expert Amazon marketplace optimization specialist. Based on the product information and market positioning strategy provided, develop a comprehensive product optimization plan to maximize performance on Amazon.

    PRODUCT INFORMATION:
    {main_product_info}

    MARKET POSITIONING STRATEGY:
    {market_positioning_suggestions}

    Please provide a detailed product optimization strategy covering the following aspects:

    1. TITLE OPTIMIZATION
    - Optimized product title following Amazon best practices
    - Keyword integration and search optimization
    - Character limit adherence and readability
    - Brand positioning integration

    2. PRODUCT DESCRIPTION OPTIMIZATION
    - Compelling product description rewrite
    - Feature and benefit highlighting
    - Pain point addressing
    - Call-to-action integration
    - SEO keyword optimization

    3. BULLET POINTS ENHANCEMENT
    - Five optimized bullet points
    - Benefit-focused messaging
    - Feature prioritization
    - Customer-centric language
    - Positioning alignment

    4. PRICING STRATEGY
    - Optimal pricing recommendations
    - Competitive pricing analysis
    - Psychological pricing tactics
    - Bundle and promotion strategies
    - Price testing recommendations

    5. IMAGE OPTIMIZATION STRATEGY
    - Main image optimization guidelines
    - Secondary image recommendations
    - Lifestyle and context images
    - Infographic and feature callouts
    - A+ Content visual strategy

    6. KEYWORD STRATEGY
    - Primary keyword identification
    - Long-tail keyword opportunities
    - Backend search term optimization
    - Category and attribute optimization
    - Seasonal keyword considerations

    7. A+ CONTENT STRATEGY
    - A+ Content module recommendations
    - Brand story integration
    - Feature comparison charts
    - Use case scenarios
    - Trust and credibility elements

    8. REVIEW OPTIMIZATION
    - Review acquisition strategies
    - Review quality improvement tactics
    - Negative review management
    - Customer feedback integration
    - Review monitoring and response

    9. INVENTORY AND FULFILLMENT
    - FBA vs FBM recommendations
    - Inventory management optimization
    - Prime eligibility maximization
    - Shipping optimization
    - Return policy optimization

    10. PERFORMANCE MONITORING
    - Key performance indicators (KPIs)
    - Tracking and analytics setup
    - A/B testing recommendations
    - Conversion optimization metrics
    - ROI measurement framework

    11. PROMOTIONAL STRATEGIES
    - Lightning deals and promotions
    - Coupon and discount strategies
    - Bundle creation opportunities
    - Cross-selling and upselling
    - Seasonal promotion planning

    12. COMPETITIVE RESPONSE
    - Competitive monitoring setup
    - Response strategies for competitor actions
    - Defensive positioning tactics
    - Market share protection
    - Innovation pipeline planning

    Format your response as a comprehensive product optimization playbook. Be specific, actionable, and data-driven. Provide clear implementation steps, expected outcomes, and success metrics. Include both immediate quick wins and long-term optimization strategies.
    """