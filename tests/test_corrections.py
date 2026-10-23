import sys
from pathlib import Path
import pandas as pd
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))
import run_02_trips as r
from run_01_build import team_panel

def test_five_point_boundary_uses_original_score(monkeypatch):
    p=pd.DataFrame({"game_id":[1,1],"season":[2023]*2,"team":["SA","PHX"],
        "is_home":[1,0],"net":[5.0000000001,-5.0000000001],"poss":[100,100],
        "city":["San Antonio"]*2,"on_trip":[False,True],"after_trip":[False]*2,
        "margin_h":[5,5]})
    monkeypatch.setattr(r.M,"own_burden",lambda p:pd.DataFrame(0.,index=p.index,
        columns=list(set(r.M.OWN.values()))))
    g=r.game_frame(p)
    assert g.margin_h.iloc[0] == 5
    assert (g.margin_h.abs() <= 5).all()
