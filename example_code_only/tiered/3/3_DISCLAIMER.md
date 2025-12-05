Vi gør det til en 3-tier ved at adskille front-end, logic og db i hver deres container. 

OPMÆRKSOM PÅ:
"the backend includes the token in its JSON replies and the frontend stores it on the client by setting a cookie"
-> Denne del er ikke implementeret korrekt i denne eksempel-kode.
-> Det kræver, at vores backend reply returnerer en validated session token i dens JSON og front-end bruger denne til at skabe en cookie. 

-> HENTYDER TIL, AT MAN KAN LOGIN_USER OG LOGOUT_USER I FRONTEND.
-> JEG MODELLERER EFTER, DET KAN FOREGÅ I BACKEND.