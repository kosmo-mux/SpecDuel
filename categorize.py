import pandas as pd
import json, re, os

csv_files = [f for f in os.listdir(".") if f.endswith(".csv")]
if not csv_files:
    print("No CSV found. Download one from Kaggle and drop it here."); exit()
csv_file = csv_files[0]
print(f"Loading: {csv_file}")
df = pd.read_csv(csv_file)
print(f"Loaded {len(df)} rows  |  Columns: {list(df.columns)}")

def col(df, *c):
    for x in c:
        if x in df.columns: return x
    return None

COL_BRAND=col(df,"Company","Brand","Manufacturer","brand")
COL_MODEL=col(df,"Product","Model","model","Name","name")
COL_TYPE=col(df,"TypeName","Type","type","Category","category")
COL_SCREEN=col(df,"Inches","Screen Size","ScreenSize","screen_size","Size")
COL_RES=col(df,"ScreenResolution","Resolution","resolution","Display")
COL_CPU=col(df,"CPU_Type","CPU","Processor","processor","cpu")
COL_CPU_CO=col(df,"CPU_Company","CPU_Brand","ProcessorBrand")
COL_GHZ=col(df,"CPU_Frequency (GHz)","CPU_Speed","GHz","cpu_ghz")
COL_RAM=col(df,"RAM (GB)","RAM","Memory (RAM)","ram","Ram (GB)")
COL_STORAGE=col(df,"Memory","Storage","HDD","SSD","storage","Hard Drive")
COL_GPU=col(df,"GPU_Type","GPU","Graphics","gpu","Video Card")
COL_GPU_CO=col(df,"GPU_Company","GPU_Brand","Graphics Brand")
COL_OS=col(df,"OpSys","OS","Operating System","os")
COL_WEIGHT=col(df,"Weight (kg)","Weight","weight","Weight_kg")
COL_PRICE_E=col(df,"Price (Euro)","Price_euros","Price (EUR)","price_eur")
COL_PRICE_U=col(df,"Price (USD)","Price_usd","Price","price","price_usd")

def safe(row,c,d=""):
    if c is None: return d
    v=row.get(c,d)
    return str(v).strip() if pd.notna(v) else d

def safe_float(row,c,d=0.0):
    if c is None: return d
    v=row.get(c,d)
    try: return float(str(v).replace("kg","").replace("GHz","").replace("$","").replace(",","").strip())
    except: return d

def safe_int(row,c,d=0):
    if c is None: return d
    v=row.get(c,d)
    try: return int(float(str(v).strip()))
    except: return d

def categorize(row):
    tn=safe(row,COL_TYPE).lower(); gpu=safe(row,COL_GPU).lower()
    gpu_co=safe(row,COL_GPU_CO).lower(); cpu=safe(row,COL_CPU).lower()
    product=safe(row,COL_MODEL).lower(); weight=safe_float(row,COL_WEIGHT,99)
    ram=safe_int(row,COL_RAM,0); inches=safe_float(row,COL_SCREEN,0)
    pe=safe_float(row,COL_PRICE_E,0); pu=safe_float(row,COL_PRICE_U,0)
    price=pu if pu>0 else pe*1.08
    is_dgpu=bool(re.search(r"gtx|rtx|rx\s?\d|radeon\s+r[579]|quadro|geforce|firepro",gpu))
    if tn=="gaming" or (is_dgpu and any(k in gpu for k in ["gtx","rtx","rx ","radeon rx"])):
        return "Desktop Replacement" if inches>=17 or weight>=3.0 else "Gaming Beast"
    if tn=="workstation" or "quadro" in gpu or "xeon" in cpu or ram>=64: return "Workstation Pro"
    if any(k in product for k in ["toughbook","toughpad","rugged","getac","durabook"]): return "Unbreakable"
    if inches>=17.3 or (inches>=15.6 and weight>=2.8): return "Desktop Replacement"
    if tn in ("ultrabook","netbook") or weight<=1.4: return "Thin & Light"
    if weight<=1.5 and inches<=14: return "Battery Champion"
    if ram>=16 and is_dgpu and price>=1200: return "Creator Studio"
    return "Best Bang for Buck"

def gpu_type(g):
    return "dGPU" if re.search(r"geforce|rtx|gtx|quadro|radeon\s+rx|radeon\s+r[579]\s|firepro|mx\d{2,3}",g,re.I) else "iGPU"

def get_vram(g,gt):
    if gt=="iGPU": return "Shared"
    for pat,v in [
        (r"RTX\s*4090","16GB GDDR6"),(r"RTX\s*408\d|RTX\s*4070\s*Ti","12GB GDDR6"),
        (r"RTX\s*4070","8GB GDDR6"),(r"RTX\s*4060","8GB GDDR6"),(r"RTX\s*4050","6GB GDDR6"),
        (r"RTX\s*3080","16GB GDDR6"),(r"RTX\s*3070","8GB GDDR6"),(r"RTX\s*3060","6GB GDDR6"),
        (r"RTX\s*3050\s*Ti","4GB GDDR6"),(r"RTX\s*3050","4GB GDDR6"),
        (r"RTX\s*2080","8GB GDDR6"),(r"RTX\s*2070","8GB GDDR6"),(r"RTX\s*2060","6GB GDDR6"),
        (r"GTX\s*1080","8GB GDDR5X"),(r"GTX\s*1070","8GB GDDR5"),
        (r"GTX\s*166\d","6GB GDDR6"),(r"GTX\s*1060","6GB GDDR5"),
        (r"GTX\s*1050\s*Ti","4GB GDDR5"),(r"GTX\s*1050","4GB GDDR5"),
        (r"GTX\s*9[78]0M","3GB GDDR5"),(r"GTX\s*9[56]0M","2GB GDDR5"),(r"GTX\s*9[234]0M","2GB DDR3"),
        (r"MX\s*5[56]\d","4GB GDDR6"),(r"MX\s*[234]\d\d","2GB GDDR5"),
        (r"Quadro\s*RTX\s*5000","16GB GDDR6"),(r"Quadro\s*RTX\s*4000","8GB GDDR6"),
        (r"Radeon\s*RX\s*68\d\dM","12GB GDDR6"),(r"Radeon\s*RX\s*67\d\dM","10GB GDDR6"),
        (r"Radeon\s*R9","4GB GDDR5"),(r"Radeon\s*R7","2GB DDR3"),
    ]:
        if re.search(pat,g,re.I): return v
    return "4GB GDDR5"

def get_gpu_score(g,gt):
    t=[(r"M4\s*Max",22000),(r"M4\s*Pro",14000),(r"M4",10000),(r"M3\s*Max",14000),
       (r"M3\s*Pro",11000),(r"M3",7800),(r"M2\s*Max",10000),(r"M2\s*Pro",9500),(r"M2",6500),
       (r"M1\s*Max",8000),(r"M1\s*Pro",7500),(r"M1",5500),(r"Arc",5800),(r"Iris\s*Xe",3500),
       (r"Iris\s*Plus",2200),(r"Iris",1800),(r"UHD\s*7[57]0",1600),(r"UHD",1200),(r"Intel\s*HD",800),
       (r"Radeon\s*780M",4200),(r"Radeon\s*760M",3500),(r"Vega\s*8",1400),(r"Vega",1200),
       (r"Adreno",6000)] if gt=="iGPU" else [
      (r"RTX\s*4090",28000),(r"RTX\s*4080",23000),(r"RTX\s*4070\s*Ti",20000),(r"RTX\s*4070",18500),
      (r"RTX\s*4060",14800),(r"RTX\s*4050",11000),(r"RTX\s*3080\s*Ti",20000),(r"RTX\s*3080",18000),
      (r"RTX\s*3070\s*Ti",16000),(r"RTX\s*3070",15000),(r"RTX\s*3060",12000),(r"RTX\s*3050\s*Ti",8500),
      (r"RTX\s*3050",8000),(r"RTX\s*2080",12000),(r"RTX\s*2070",10000),(r"RTX\s*2060",8500),
      (r"GTX\s*1660\s*Ti",7000),(r"GTX\s*1660",6500),(r"GTX\s*1650\s*Ti",5500),(r"GTX\s*1650",5000),
      (r"GTX\s*1080",8000),(r"GTX\s*1070",7000),(r"GTX\s*1060",5500),(r"GTX\s*1050\s*Ti",4000),
      (r"GTX\s*1050",3500),(r"GTX\s*980M",4000),(r"GTX\s*970M",3500),(r"GTX\s*960M",2800),
      (r"GTX\s*950M",2500),(r"GTX\s*940M",2000),(r"Quadro\s*RTX\s*5000",17000),
      (r"Radeon\s*RX\s*68\d\dM",15000),(r"Radeon\s*RX\s*67\d\dM",12000),
      (r"MX\s*5[56]\d",4500),(r"MX\s*4[56]\d",3200),(r"MX\s*3[35]\d",2800),(r"MX\s*1[35]\d",1800)]
    for pat,score in t:
        if re.search(pat,g,re.I): return score
    return 1000 if gt=="iGPU" else 2000

def get_battery(cpu,cat,tp):
    c=cpu.lower(); base=8
    if re.search(r"\by\b|[45]500u|[45]700u|7[57]30u",c): base=16
    elif re.search(r"\bu\b|ultra [35]|core m|snapdragon|apple m",c): base=14
    elif re.search(r"ultra [79]",c): base=12
    elif re.search(r"hx|hk",c): base=4
    elif re.search(r"\bh\b",c): base=6
    elif re.search(r"\bp\b",c): base=10
    if cat=="Battery Champion": base=max(base,14)+4
    if cat in ("Gaming Beast","Desktop Replacement"): base=min(base,6)
    if tp.lower() in ("ultrabook","netbook"): base+=2
    return min(28,max(3,base))

laptops=[]; skipped=0
for _,row in df.iterrows():
    brand=safe(row,COL_BRAND); model=safe(row,COL_MODEL)
    if not brand or not model or brand=="nan" or model=="nan": skipped+=1; continue
    cpu=safe(row,COL_CPU); cpu_co=safe(row,COL_CPU_CO)
    gpu=(safe(row,COL_GPU_CO)+" "+safe(row,COL_GPU)).strip()
    tp=safe(row,COL_TYPE,"Notebook"); cat=categorize(row); gt=gpu_type(gpu)
    pe=safe_float(row,COL_PRICE_E,0); pu=safe_float(row,COL_PRICE_U,0)
    price=round(pu if pu>0 else pe*1.08,2)
    ghz=safe(row,COL_GHZ); ghz=ghz+" GHz" if ghz and "GHz" not in ghz else ghz
    wt=safe(row,COL_WEIGHT); wt=wt+" kg" if wt and "kg" not in wt else wt
    laptops.append({"brand":brand,"model":model,"category":cat,"type":tp,
        "screen":safe(row,COL_SCREEN)+chr(34),"resolution":safe(row,COL_RES),
        "cpu":(cpu_co+" "+cpu).strip() if cpu_co else cpu,"cpu_ghz":ghz,
        "ram":str(safe_int(row,COL_RAM))+" GB","storage":safe(row,COL_STORAGE),
        "gpu":gpu,"gpu_type":gt,"vram":get_vram(gpu,gt),"gpu_score":get_gpu_score(gpu,gt),
        "battery_hours":get_battery(cpu,cat,tp),"os":safe(row,COL_OS),
        "weight":wt,"price_usd":price})

from collections import Counter
print("\nCategory breakdown:")
for cat,n in Counter(l["category"] for l in laptops).most_common(): print(f"  {cat}: {n}")
print(f"\nBuilt {len(laptops)} laptops ({skipped} skipped)")

existing=[]
if os.path.exists("laptops_2.json"):
    with open("laptops_2.json","r",encoding="utf-8-sig") as f: existing=json.load(f)
    print(f"Existing library: {len(existing)}")
keys={(l["brand"].lower(),l["model"].lower()) for l in existing}
new=[l for l in laptops if (l["brand"].lower(),l["model"].lower()) not in keys]
print(f"New laptops to add: {len(new)}")
combined=existing+new
with open("laptops_2.json","w",encoding="utf-8") as f: json.dump(combined,f,indent=2,ensure_ascii=False,default=str)
print(f"\nDone! laptops_2.json: {len(combined)} total")
print("Upload laptops_2.json to Netlify to go live!")