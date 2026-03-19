"""
Preconfigured prompts for different video analysis scenarios.
Set the 'scenario' key in your secret to switch between them.
"""

SCENARIO_PROMPTS = {
    "surveillance": """Analyze this surveillance footage and describe:
1) All visible people, their actions, behaviors, and any unusual movements or interactions
2) Any safety hazards including fire, smoke, or environmental dangers
3) Objects of interest such as abandoned items, vehicles, or equipment
4) Group dynamics including crowd formations, gatherings, or confrontations
5) Any signs of distress, emergency situations, or security concerns
Be specific about locations, timing, and severity.
IMPORTANT: Keep your response concise (under 150 words) and always write complete sentences.""",

    "traffic": """Analyze this traffic camera footage and describe:
1) Vehicle movements, types, and traffic flow patterns
2) Any traffic violations: running red lights, illegal turns, speeding indicators
3) Pedestrian activity and crosswalk usage
4) Traffic congestion levels and bottlenecks
5) Any accidents, near-misses, or dangerous driving behaviors
6) Road conditions and visibility factors
Be specific about vehicle types, directions, and timing of events.
IMPORTANT: Keep your response concise (under 150 words) and always write complete sentences.""",

    "nhl": """Analyze this NHL hockey game footage and describe:
1) Key plays: goals, shots on goal, saves, assists, and scoring chances
2) Player actions: skating, passing, shooting, checking, and positioning
3) Penalties and infractions observed
4) Goaltender performance and positioning
5) Power play or penalty kill situations
6) Face-offs, puck possession, and zone entries
7) Team formations and strategic plays
Identify jersey numbers and team colors when visible. Note the pace and flow of play.
IMPORTANT: Keep your response concise (under 150 words) and always write complete sentences.""",

    "sports": """Analyze this sports footage and describe:
1) Key game actions and plays occurring
2) Player movements, techniques, and performance
3) Scoring opportunities and defensive plays
4) Team formations and strategic positioning
5) Any fouls, violations, or referee decisions
6) Game momentum and critical moments
7) Notable individual performances
Be specific about player positions, timing, and the sequence of events.
IMPORTANT: Keep your response concise (under 150 words) and always write complete sentences.""",

    "retail": """Analyze this retail store footage and describe:
1) Customer traffic patterns and store flow
2) Shopping behaviors and product interactions
3) Queue lengths and checkout activity
4) Staff presence and customer service interactions
5) Any suspicious activities or potential theft indicators
6) Store organization and display effectiveness
7) Peak activity periods and crowd density
Be specific about locations within the store and timing of events.
IMPORTANT: Keep your response concise (under 150 words) and always write complete sentences.""",

    "warehouse": """Analyze this warehouse footage and describe:
1) Forklift and equipment movements and safety compliance
2) Worker activities and task execution
3) Inventory handling and storage operations
4) Safety protocol adherence (PPE, walkways, loading zones)
5) Any hazards, spills, or unsafe conditions
6) Efficiency of movement patterns and workflows
7) Loading/unloading dock activities
Be specific about equipment types, locations, and timing.
IMPORTANT: Keep your response concise (under 150 words) and always write complete sentences.""",

    "egocentric": """Analyze this first-person (egocentric) video footage and describe:
1) Hand movements, gestures, and object manipulations (cooking, tool usage, item handling)
2) Kitchen activities: food preparation, cooking techniques, ingredient usage, and kitchen tool interactions
3) Barista work: coffee preparation steps, equipment usage, drink assembly, and customer service actions
4) Sports activities: athletic movements, techniques, equipment handling, and performance actions from first-person perspective
5) Object finding and searching: what items are being located, search patterns, and object interactions
6) Tool and equipment usage: specific tools being used, how they are manipulated, and task execution
7) Environmental context: workspace layout, objects in view, and spatial relationships
8) Task progression: step-by-step actions and workflow sequences
Be specific about hand positions, object locations, and the sequence of actions from the wearer's perspective.
IMPORTANT: Keep your response concise (under 150 words) and always write complete sentences.""",

    "general": """Analyze this video footage and describe:
1) All people visible and their actions
2) Objects and items of interest
3) Environmental conditions and setting
4) Any notable events or activities
5) Movement patterns and interactions
Be specific and factual about what is observed.
IMPORTANT: Keep your response concise (under 150 words) and always write complete sentences.""",

    "nyc_control": """Analyze this NYC urban footage for real-time command and control.
Output your analysis as a readable text summary (strictly NO JSON, NO code blocks).

Please describe the scene in the following format:

1. OVERVIEW:
   - Identify the exact location (streets, intersections, landmarks).
   - Summarize the general atmosphere (calm, chaotic, congested).

2. DETAILS (TEXT & ID):
   - List any readable License Plates or TLC Medallions found.
   - Quote relevant storefront signage or street signs.

3. ANOMALY:
   - Describe any traffic violations (double parking, illegal turns).
   - Describe any disorderly conduct or public safety hazards.
   - Identify specific vehicles of interest (Police, Fire, Sanitation).

4. REASONING:
   - Explain what is actually happening in the scene.
   - Assess if the situation is under control or requires monitoring.

Write in a direct, professional, and observational tone.
IMPORTANT: Keep your response concise (under 150 words) and always write complete sentences."""
}




DEFAULT_SCENARIO = "general"


def get_prompt_for_scenario(scenario: str) -> str:
    """
    Get the appropriate prompt for a given scenario.
    Falls back to 'general' if scenario is not found.
    
    Args:
        scenario: The scenario key (surveillance, traffic, nhl, sports, etc.)
    
    Returns:
        The prompt string for that scenario
    """
    scenario_lower = scenario.lower().strip()
    
    if scenario_lower in SCENARIO_PROMPTS:
        return SCENARIO_PROMPTS[scenario_lower]
    
    # Log warning and fall back to general
    import logging
    logging.warning(f"[PROMPTS] Unknown scenario '{scenario}', falling back to 'general'")
    return SCENARIO_PROMPTS["general"]


def get_available_scenarios() -> list[str]:
    """Return list of all available scenario keys"""
    return list(SCENARIO_PROMPTS.keys())

