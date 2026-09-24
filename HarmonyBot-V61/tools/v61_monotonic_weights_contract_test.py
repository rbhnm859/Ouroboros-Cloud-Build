#!/usr/bin/env python3
weights={"Trend":[.40,.30,.20,.10],"Exhaustion":[.65,.35],"Transition":[.50,.30,.20]}
for k,w in weights.items(): assert abs(sum(w)-1.0)<1e-12,(k,sum(w)); assert all(w[i]>=w[i+1] for i in range(len(w)-1)),k
print("V61 monotonic route-risk weights contract PASS")
