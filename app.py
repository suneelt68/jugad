from fastapi import FastAPI
from jugaad_data.nse import NSELive


app = FastAPI()

@app.get("/liveoptionchain")
def get_live_optionChain():
  n = NSELive()
  return n.index_option_chain("NIFTY")
