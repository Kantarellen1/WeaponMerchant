import os
import json
import argparse
import shutil

def slug(s: str) -> str:
    return "".join(c if c.isalnum() else "_" for c in s.strip().lower()).strip("_")

def process_file(path, apply, url_base):
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        print(f"SKIP (invalid json): {path} -> {e}")
        return False

    name = data.get("name")
    if not name:
        print(f"SKIP (no name): {path}")
        return False

    merchant_id = slug(name)
    print(f"{path} -> name: '{name}'  merchant_id: '{merchant_id}'")

    if apply:
        bak = path + ".bak"
        if not os.path.exists(bak):
            shutil.copy2(path, bak)
        changed = False
        if data.get("merchant_id") != merchant_id:
            data["merchant_id"] = merchant_id
            changed = True
        if url_base:
            url = f"{url_base.rstrip('/')}/{merchant_id}"
            if data.get("url") != url:
                data["url"] = url
                changed = True
        if changed:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print(f"  UPDATED -> merchant_id/url written (backup at {bak})")
    return True

def walk_and_process(lore_root, apply, url_base):
    country_root = os.path.join(lore_root, "country_lore")
    # country_lore structure
    if os.path.isdir(country_root):
        for country in os.listdir(country_root):
            town_base = os.path.join(country_root, country, "town_lore")
            if not os.path.isdir(town_base):
                continue
            for town in os.listdir(town_base):
                town_folder = os.path.join(town_base, town)
                if not os.path.isdir(town_folder):
                    continue
                for fname in os.listdir(town_folder):
                    if fname.lower().endswith(".json"):
                        process_file(os.path.join(town_folder, fname), apply, url_base)

    # legacy town_lore layout
    legacy = os.path.join(lore_root, "town_lore")
    if os.path.isdir(legacy):
        for town in os.listdir(legacy):
            town_folder = os.path.join(legacy, town)
            if not os.path.isdir(town_folder):
                continue
            for fname in os.listdir(town_folder):
                if fname.lower().endswith(".json"):
                    process_file(os.path.join(town_folder, fname), apply, url_base)

if __name__ == "__main__":
    p = argparse.ArgumentParser(description="List / sync merchant_id fields in lore JSON files")
    p.add_argument("--apply", action="store_true", help="Write merchant_id (and url) into JSON files")
    p.add_argument("--url-base", default="http://127.0.0.1:8000/talk_to_merchant", help="Base for url field (optional)")
    args = p.parse_args()

    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    lore_root = os.path.join(repo_root, "lore")
    if not os.path.isdir(lore_root):
        print("lore folder not found at expected location:", lore_root)
        raise SystemExit(1)

    print("Scanning lore files... (apply=%s, url_base=%s)" % (args.apply, args.url_base))
    walk_and_process(lore_root, args.apply, args.url_base if args.apply else None)
    print("Done.")