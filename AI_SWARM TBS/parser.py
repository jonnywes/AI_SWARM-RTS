# parser.py
import constants

def parse_llm_command(text):
    """Parses the LLM output and validates it against the new Macro Objectives."""
    lines = text.strip().split('\n')
    
    target = None
    action = None
    remarks = ""
    
    in_remarks = False
    
    for line in lines:
        line = line.strip()
        
        if line.startswith("TARGET UNIT:"):
            target = line.replace("TARGET UNIT:", "").strip()
        elif line.startswith("ACTION:"):
            action = line.replace("ACTION:", "").strip()
        elif line.startswith("REMARKS:"):
            in_remarks = True
            remarks = line.replace("REMARKS:", "").strip()
        elif in_remarks:
            remarks += " " + line

    # Validation Checks
    if not target or not action:
        return {"status": "error", "message": "Formatting Error: Missing TARGET UNIT or ACTION."}
        
    if target != constants.TARGET_QUEEN:
        return {"status": "error", "message": f"Target Error: Invalid target '{target}'."}
        
    # Strictly enforce the new macro-objectives
    valid_action_found = False
    for valid_action in constants.VALID_ACTIONS:
        if valid_action.lower() in action.lower():
            action = valid_action # Normalize it exactly to the constant
            valid_action_found = True
            break
            
    if not valid_action_found:
        return {
            "status": "error", 
            "message": f"Action Error: '{action}' is invalid. You MUST use 'Set Objective: Balanced', 'Set Objective: Aggressive', or 'Set Objective: Economy'."
        }
        
    return {
        "status": "success",
        "target": target,
        "action": action,
        "remarks": remarks
    }