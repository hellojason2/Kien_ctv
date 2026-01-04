def validate_ctv_data(ctv_list):
    """
    DOES: Validate CTV import data for circular references and missing fields
    """
    for ctv in ctv_list:
        if not ctv.get('ma_ctv'):
            return False, "Missing required field: ma_ctv"
        if not ctv.get('ten'):
            return False, f"Missing required field: ten for CTV {ctv.get('ma_ctv')}"
    
    ctv_codes = {ctv['ma_ctv'] for ctv in ctv_list}
    
    def has_cycle(start, visited, rec_stack, ref_map):
        visited.add(start)
        rec_stack.add(start)
        
        parent = ref_map.get(start)
        if parent:
            if parent in rec_stack:
                return True
            if parent not in visited:
                if has_cycle(parent, visited, rec_stack, ref_map):
                    return True
        
        rec_stack.remove(start)
        return False
    
    ref_map = {ctv['ma_ctv']: ctv.get('nguoi_gioi_thieu') for ctv in ctv_list}
    visited = set()
    
    for ctv_code in ctv_codes:
        if ctv_code not in visited:
            if has_cycle(ctv_code, visited, set(), ref_map):
                return False, f"Circular reference detected involving CTV {ctv_code}"
    
    return True, None

