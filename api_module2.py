import os
import sys
import importlib.util

module2_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Module-2")
sys.path.insert(0, module2_dir)

# Import the classifier.py from Module-2 dynamically because of the dash in folder name
spec = importlib.util.spec_from_file_location("classifier_mod", os.path.join(module2_dir, "classifier.py"))
classifier_mod = importlib.util.module_from_spec(spec)
# Patch print to avoid console spam if we want, but letting it print is fine for logs.
spec.loader.exec_module(classifier_mod)


def classify_image(image_path, forced_cat=None):
    """
    Classifies an image using Module-2's pipeline.
    Returns a dictionary with the results.
    """
    if not os.path.exists(image_path):
        return {"success": False, "error": f"Image not found: {image_path}"}

    # 1. Detect Category
    try:
        primary_cat, clip_conf, clip_scores, clip_method = classifier_mod._detect_category(image_path, forced_cat)
    except Exception as e:
        return {"success": False, "error": f"Category routing failed: {str(e)}"}

    # 2. Find Runnable Module
    run_cat, is_fallback = classifier_mod._find_runnable_module(primary_cat)
    if run_cat is None:
        return {
            "success": False,
            "error": "No detection module is available for any category. Ensure .pth models are present."
        }

    # 3. Run specific detector
    try:
        # Prevent namespace collision with Module-1's 'src' folder
        import sys
        
        # Temporarily hide Module-1 from sys.path
        removed_paths = []
        for p in list(sys.path):
            if "Module-1" in p:
                removed_paths.append(p)
                sys.path.remove(p)
                
        # Pop src and all its submodules from sys.modules
        popped_modules = {}
        for mod_name in list(sys.modules.keys()):
            if mod_name == 'src' or mod_name.startswith('src.'):
                popped_modules[mod_name] = sys.modules.pop(mod_name)
        
        result = classifier_mod.MODULE_RUNNERS[run_cat](image_path)
        
        # Clean up Module-2's src modules that just got loaded
        for mod_name in list(sys.modules.keys()):
            if mod_name == 'src' or mod_name.startswith('src.'):
                sys.modules.pop(mod_name)
                
        # Restore sys.path and sys.modules
        for p in reversed(removed_paths):
            sys.path.insert(0, p)
            
        for mod_name, mod_val in popped_modules.items():
            sys.modules[mod_name] = mod_val
    except Exception as exc:
        result = {
            "detector": classifier_mod.MODULE_INFO[run_cat]["name"],
            "verdict": None,
            "confidence": 0.0,
            "ai_probability": 0.5,
            "real_probability": 0.5,
            "reasons": [f"Unexpected error: {exc}"],
            "raw": {},
            "error": str(exc),
        }

    return {
        "success": True,
        "detected_category": primary_cat,
        "clip_confidence": clip_conf,
        "is_fallback": is_fallback,
        "run_category": run_cat,
        "result": result
    }
