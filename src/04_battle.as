// =====================================================================
//  Rehauled battle systems:
//   - wind (changes every turn, shown on the HUD)
//   - enemy AI that simulates its shot and "zeroes in" over time
//   - two new ammo types: TRIPLE SHOT and MEGA BOMB (slots 4 and 5)
//   - aim scope (trajectory preview, bought in the shop)
//   - time-of-day palettes, snow, shadows, trails, shockwaves
//   - headshot / splash bonuses, slow-motion final knockout
// =====================================================================
_global.RH_AMMO = [null,"snowball","grenade","rocket","triple","mega"];
_global.RH_ARMOR = [1,0.85,0.72,0.6];
_global.RH_SCOPE = [0,28,50,80];

// sky / background / foreground colour transforms: [rMul,rOff,gMul,gOff,bMul,bOff]
_global.RH_PAL = {snow:{sky:[0.86,10,0.95,12,1.12,14],bg:[0.9,8,0.95,10,1.08,14],fg:[0.96,4,0.98,4,1.04,8],snow:true},afternoon:{sky:[1.06,6,1,0,0.86,0],bg:[1.04,4,1,0,0.9,0],fg:[1.02,0,1,0,0.95,0]},golden:{sky:[1.3,50,1,8,0.62,8],bg:[1.1,10,0.97,2,0.8,0],fg:[1.06,4,1,0,0.9,0]},sunset:{sky:[1.18,32,0.78,6,0.8,24],bg:[1.04,10,0.86,0,0.86,8],fg:[1.03,4,0.93,0,0.93,3]},dusk:{sky:[0.62,20,0.58,10,0.98,42],bg:[0.7,6,0.7,8,0.92,18],fg:[0.86,0,0.86,0,1,8]}};
_global.RH_LEVELPAL = ["day","snow","day","afternoon","afternoon","golden","golden","snow","sunset","sunset","dusk"];

// ----------------------------------------------------------- level setup
// called from start() right after levelInit()
rhLevelStart = function()
{
   var D = rhD();
   var lv = rhClamp(currentLevel,1,11);
   game.rhBonus = 0;
   game.rhHeadshots = 0;
   game.rhSlow = 0;
   game.rhWind = 0;
   game.rhAIErrMul = 1;
   game.rhEnemyTough = 1;
   var wmax = _global.RH_WIND[lv - 1];
   game.rhPal = _global.RH_LEVELPAL[lv - 1];
   if(rhIsEndless())
   {
      var w = _global.RH.wave;
      wmax = Math.min(0.055,0.012 + 0.004 * w);
      game.rhAIErrMul = Math.max(0.5,1 - 0.035 * (w - 1));
      game.rhEnemyTough = 1 + 0.08 * (w - 1);
      var pals = ["day","afternoon","golden","sunset","dusk","snow"];
      game.rhPal = pals[(w - 1) % pals.length];
   }
   game.rhWindMax = wmax * D.windMul;
   level.triples = rhNum(_global.saveProgress.triples);
   level.megas = rhNum(_global.saveProgress.megas);
   level.player1.triples = level.triples;
   level.player1.megas = level.megas;
};

rhNewTurnWind = function()
{
   if(game.rhWindMax > 0)
   {
      game.rhWind = (Math.random() * 2 - 1) * game.rhWindMax;
   }
   else
   {
      game.rhWind = 0;
   }
   rhUpdateHud();
};

rhCT = function(a)
{
   return new flash.geom.ColorTransform(a[0],a[2],a[4],1,a[1],a[3],a[5],0);
};

rhTintColor = function(c, a)
{
   var r = c >> 16 & 255;
   var g = c >> 8 & 255;
   var b = c & 255;
   r = rhClamp(Math.round(r * a[0] + a[1]),0,255);
   g = rhClamp(Math.round(g * a[2] + a[3]),0,255);
   b = rhClamp(Math.round(b * a[4] + a[5]),0,255);
   return r << 16 | g << 8 | b;
};

rhSeaColor = function(c)
{
   var p = _global.RH_PAL[game.rhPal];
   if(p == undefined)
   {
      return c;
   }
   return rhTintColor(c,p.bg);
};

// called at the end of start(), after every clip of the battle exists
rhBattleDecorate = function()
{
   var p = _global.RH_PAL[game.rhPal];
   if(p != undefined)
   {
      sky.transform.colorTransform = rhCT(p.sky);
      main.achtergrond.transform.colorTransform = rhCT(p.bg);
      main.achtergrondStrand.transform.colorTransform = rhCT(p.bg);
      var fg = ["raftsAchter","raftsVoor","pinguinContainer","pinguinContainerVoor","haaiContainer"];
      var i = 0;
      while(i < fg.length)
      {
         main[fg[i]].transform.colorTransform = rhCT(p.fg);
         i++;
      }
      if(p.snow == true)
      {
         rhStartSnow();
      }
   }
   var shadow = new flash.filters.DropShadowFilter(4,70,0,0.32,5,5,1,1);
   var j = 0;
   while(j < game.objects.length)
   {
      game.objects[j].mc.filters = [shadow];
      j++;
   }
   j = 0;
   while(j < game.objectsOverig.length)
   {
      game.objectsOverig[j].mc.filters = [shadow];
      j++;
   }
   main.actionContainer.createEmptyMovieClip("rhTrail",-16000);
   rhBuildHud();
};

rhCleanupBattle = function()
{
   _root.rhWeather.removeMovieClip();
   _root.rhModalBattle.removeMovieClip();
};

rhStartSnow = function()
{
   var w = _root.createEmptyMovieClip("rhWeather",6);
   w.flakes = [];
   var i = 0;
   while(i < 46)
   {
      var f = w.attachMovie("mcSnowflake","f" + i,i);
      f.gotoAndStop(1 + random(3));
      f._x = random(640);
      f._y = random(480);
      f._xscale = f._yscale = 120 + random(120);
      f._alpha = 55 + random(40);
      f.vy = 1 + Math.random() * 2.2;
      f.ph = Math.random() * 6;
      w.flakes.push(f);
      i++;
   }
   w.lastScroll = scrollPos;
   w.onEnterFrame = function()
   {
      var ds = scrollPos - this.lastScroll;
      this.lastScroll = scrollPos;
      var k = 0;
      while(k < this.flakes.length)
      {
         var f = this.flakes[k];
         f.ph += 0.05;
         f._y += f.vy;
         f._x += Math.sin(f.ph) * 0.6 + game.rhWind * 60 - ds * (0.5 + f.vy / 6);
         if(f._y > 480)
         {
            f._y = -6;
            f._x = random(640);
         }
         if(f._x < -10)
         {
            f._x += 650;
         }
         else if(f._x > 650)
         {
            f._x -= 660;
         }
         k++;
      }
   };
};

// --------------------------------------------------------------- HUD
rhBuildHud = function()
{
   hud.rhHud.removeMovieClip();
   var h = hud.createEmptyMovieClip("rhHud",500);
   var wp = h.createEmptyMovieClip("wind",1);
   wp._x = 400;
   wp._y = 10;
   rhRect(wp,-55,0,110,44,12,1714764,62,16777215,70);
   var t = rhText(wp,"lbl",2,-55,1,110,20,"WIND",12,16777215,"center");
   wp.val = rhText(wp,"val",3,-55,24,110,20,"",12,16776960,"center");
   rhOutline(wp.val,2);
   wp.arrow = wp.createEmptyMovieClip("arrow",4);
   wp.arrow._y = 23;
   h.info = rhText(h,"info",5,297,58,280,22,"",12,16777215,"center");
   rhOutline(h.info,3);
   h.preview = h.createEmptyMovieClip("preview",6);
   h.bars = h.createEmptyMovieClip("bars",7);
   rhUpdateHud();
};

rhUpdateHud = function()
{
   var h = hud.rhHud;
   if(h == undefined || game.tussenscherm == true)
   {
      return undefined;
   }
   var vis = rhHudFree();
   h.wind._visible = vis;
   h.info._visible = vis;
   var w = rhNum(game.rhWind);
   var a = h.wind.arrow;
   a.clear();
   var n = Math.round(Math.abs(w) * 500);
   if(n == 0)
   {
      h.wind.val.text = "CALM";
   }
   else
   {
      h.wind.val.text = String(n);
      var len = 10 + Math.min(40,n * 1.6);
      var dir = w > 0 ? 1 : -1;
      a.lineStyle(4,16776960,100);
      a.moveTo(- dir * len / 2,0);
      a.lineTo(dir * len / 2,0);
      a.lineStyle();
      a.beginFill(16776960,100);
      a.moveTo(dir * (len / 2 + 7),0);
      a.lineTo(dir * (len / 2 - 3),-6);
      a.lineTo(dir * (len / 2 - 3),6);
      a.endFill();
      a._x = 0;
   }
   var s = "";
   if(rhIsEndless())
   {
      s = "WAVE " + _global.RH.wave + "   LIVES " + Math.max(0,_global.progress.lives);
   }
   if(_global.RHset.ff == true)
   {
      s += (s == "" ? "" : "   ") + ">> FAST";
   }
   h.info.text = s;
};

// the wind panel hides while the big level / result banners are up
rhHudFree = function()
{
   return hud.mcBeginMessage == undefined && hud.mcFinishMessage == undefined;
};

rhLetterbox = function(on)
{
   var b = hud.rhHud.bars;
   if(b == undefined)
   {
      return undefined;
   }
   if(b.hh == undefined)
   {
      b.hh = 0;
   }
   b.hh += on ? (38 - b.hh) / 4 : (0 - b.hh) / 3;
   b.clear();
   if(b.hh > 0.5)
   {
      b.beginFill(0,100);
      b.moveTo(0,0);
      b.lineTo(640,0);
      b.lineTo(640,b.hh);
      b.lineTo(0,b.hh);
      b.endFill();
      b.beginFill(0,100);
      b.moveTo(0,480 - b.hh);
      b.lineTo(640,480 - b.hh);
      b.lineTo(640,480);
      b.lineTo(0,480);
      b.endFill();
   }
};

// --------------------------------------------------------- main frame
rhFrame = function()
{
   if(hud.rhHud.wind._visible != rhHudFree())
   {
      rhUpdateHud();
   }
   if(game.rhSlow > 0)
   {
      game.rhSlow--;
      rhLetterbox(true);
      if(game.rhSlow % 3 == 0)
      {
         mainLoop();
      }
      rhTrailsUpdate();
      return undefined;
   }
   rhLetterbox(false);
   mainLoop();
   if(_global.RHset.ff == true && game.endOfGame != true)
   {
      mainLoop();
   }
   rhTrailsUpdate();
};

rhTrailsUpdate = function()
{
   var tc = main.actionContainer.rhTrail;
   if(tc == undefined)
   {
      return undefined;
   }
   tc.clear();
   var i = 0;
   while(i < game.cannonBalls.length)
   {
      var b = game.cannonBalls[i];
      if(b.rhTrailColor != undefined)
      {
         if(b.rhTr == undefined)
         {
            b.rhTr = [];
         }
         b.rhTr.push({x:b.p1.x,y:b.p1.y});
         if(b.rhTr.length > 16)
         {
            b.rhTr.shift();
         }
         var n = b.rhTr.length;
         var k = 1;
         while(k < n)
         {
            var f = k / n;
            tc.lineStyle(1 + f * b.rhTrailW,b.rhTrailColor,f * 55);
            tc.moveTo(b.rhTr[k - 1].x,b.rhTr[k - 1].y);
            tc.lineTo(b.rhTr[k].x,b.rhTr[k].y);
            k++;
         }
      }
      i++;
   }
};

// ------------------------------------------------------------ physics
// Mirrors initObject() + the wind applied in mainLoop(). Returns the x
// where the shot comes down through height targetY, or null if it never does.
rhSimLand = function(x, y, vx, vy, m, airf, wind, targetY, maxSteps)
{
   var g = game.g * m;
   vy += g;
   x += vx;
   y += vy;
   vx *= airf;
   vy *= airf;
   var i = 0;
   var px;
   var py;
   while(i < maxSteps)
   {
      px = x;
      py = y;
      vx += wind;
      vy += g;
      x += vx;
      y += vy;
      vx *= airf;
      vy *= airf;
      if(vy > 0 && py < targetY && y >= targetY)
      {
         return px + (x - px) * (targetY - py) / (y - py);
      }
      if(y > 900)
      {
         return null;
      }
      i++;
   }
   return null;
};

rhAmmoPhysics = function(ammo)
{
   if(ammo == "grenade")
   {
      return {m:1.2,airf:0.994};
   }
   if(ammo == "mega")
   {
      return {m:1.3,airf:0.994};
   }
   if(ammo == "rocket")
   {
      return {m:0.9,airf:0.995};
   }
   return {m:1.1,airf:0.995};
};

// ------------------------------------------------------------------ AI
rhLivingCrew = function(raftnr)
{
   var out = [];
   var r = game["raft" + raftnr];
   var i = 0;
   while(i < r.occupants.length)
   {
      var o = game.objects[r.occupants[i]];
      if(o != undefined && o.deceased != true && o.health > 0)
      {
         out.push(o);
      }
      i++;
   }
   return out;
};

rhAIChooseTarget = function()
{
   var front = getMostLeftPenguin(1);
   var crew = rhLivingCrew(1);
   if(crew.length <= 1)
   {
      return front;
   }
   var d = _global.RH.diff;
   if(d == 2)
   {
      // hard: go for the weakest crew member
      var best = front;
      var i = 0;
      while(i < crew.length)
      {
         if(crew[i].health < best.health)
         {
            best = crew[i];
         }
         i++;
      }
      return best;
   }
   var pick = d == 0 ? 0.4 : 0.25;
   if(Math.random() < pick)
   {
      return crew[random(crew.length)];
   }
   return front;
};

rhAIPower = function(lx, ly, rad, m, airf)
{
   var t = game.rhAITarget;
   if(t == undefined || t.deceased == true || rhIndexOf(game.objects,t) < 0)
   {
      t = getMostLeftPenguin(1);
   }
   if(t == null || t == undefined)
   {
      return _global.cannonPower;
   }
   var D = rhD();
   var tx = t.p0.x;
   var ty = t.p0.y - 25;
   var w = game.rhWind * D.aiWind;
   var cx = Math.cos(rad) / 3;
   var cy = Math.sin(rad) / 3;
   var lo = 4;
   var hi = 150;
   var i = 0;
   var mid;
   var x;
   while(i < 24)
   {
      mid = (lo + hi) / 2;
      x = rhSimLand(lx,ly,mid * cx,mid * cy,m,airf,w,ty,700);
      var shortShot;
      if(x == null)
      {
         shortShot = true;
      }
      else if(cx < 0)
      {
         shortShot = x > tx;
      }
      else
      {
         shortShot = x < tx;
      }
      if(shortShot)
      {
         lo = mid;
      }
      else
      {
         hi = mid;
      }
      i++;
   }
   var p = (lo + hi) / 2;
   var n = rhClamp(game.AIshotsFired,1,30);
   var lv = rhIsEndless() ? 6 : rhClamp(currentLevel,1,11);
   var emin = 0.06 - 0.0045 * (lv - 1);
   var E = (0.12 * Math.pow(0.6,n - 1) + emin) * D.aiErr * game.rhAIErrMul;
   p *= 1 + (Math.random() * 2 - 1) * E;
   game.rhLastAI = {target:tx,ideal:(lo + hi) / 2,power:p,err:E};
   if(isNaN(p))
   {
      return _global.cannonPower;
   }
   return rhClamp(p,4,150);
};

// ---------------------------------------------------------- projectiles
// Replacement body of attachSnowball(); supports several shots in flight.
rhSpawnShot = function(loopMc, ai, optie, angleOffset, ammo, follow)
{
   var idNm;
   var airf;
   var m;
   var bb;
   var explosief = false;
   var mega = false;
   var type = ammo;
   if(ai == true)
   {
      if(ammo == "explosiefProjectiel" && level.opponent != "savage")
      {
         idNm = "mcTurtle";
      }
      else
      {
         idNm = "ammo_" + level.opponent;
      }
      if(ammo == "explosiefProjectiel")
      {
         explosief = true;
      }
      airf = 0.99;
      m = 0.88;
      bb = 0.8;
      if(level.opponent == "savage" || level.opponent == "chinees" || level.opponent == "viking")
      {
         speelSimpelSFX("launch_arrow");
      }
      else
      {
         speelSimpelSFX("snowball");
      }
   }
   else if(ammo == "grenade" || ammo == "mega")
   {
      explosief = true;
      idNm = "mcGrenade";
      type = "grenade";
      airf = 0.994;
      m = 1.2;
      bb = 0.7;
      if(ammo == "mega")
      {
         mega = true;
         m = 1.3;
         bb = 0.55;
      }
      speelSimpelSFX("grenade");
   }
   else if(ammo == "rocket")
   {
      explosief = true;
      idNm = "mcRocket";
      airf = 0.995;
      m = 0.9;
      bb = 0.8;
      speelSimpelSFX("rocket");
   }
   else
   {
      idNm = "mcSnowball";
      type = "snowball";
      airf = 0.995;
      m = 1.1;
      bb = 0.8;
      if(follow != false || ammo != "triple")
      {
         speelSimpelSFX("snowball");
      }
   }
   var rotDeg = ai == true ? _global.oppCannonRotation : _global.cannonRotation;
   rotDeg += angleOffset;
   var d = main.actionContainer.getNextHighestDepth();
   var mc = main.actionContainer.attachMovie(idNm,"ball" + d,d);
   var o = {f:1,m:m,r:24,b:bb,rot:0,stopTerrainHittest:false,airf:airf,arrayNr:game.cannonBalls.length,mc:mc,sb:true,timesColl:0,idNm:idNm,timesHitAnything:0,explosief:explosief,type:type,fireScrollPos:scrollPos,aantMannetjeHits:0};
   o.mega = mega;
   o.ammo = ammo;
   o.rhHit = [];
   game.cannonBalls.push(o);
   if(optie != "instructions" && follow != false)
   {
      cannonBallToFollow = o;
   }
   o.mannetjeGeraakt = false;
   o.aiShot = ai == true;
   var rad = rotDeg * 0.017453292519943295;
   hitTestBounds(loopMc.loopPoint,main);
   var lx = loopMc.loopPoint.xMin + Math.cos(rad) * 20;
   var ly = loopMc.loopPoint.yMin + Math.sin(rad) * 20;
   if(ai == true)
   {
      _global.cannonPower = rhAIPower(lx,ly,rad,m,airf);
   }
   if(isNaN(_global.cannonPower))
   {
      _global.cannonPower = 60;
   }
   o.vx = _global.cannonPower * Math.cos(rad) / 3;
   o.vy = _global.cannonPower * Math.sin(rad) / 3;
   o.rot = 0.3 + Math.random() * 0.7;
   if(o.vx < 0)
   {
      o.rot *= -1;
   }
   if(type == "grenade")
   {
      o.counter = mega ? 90 : 115;
      o.rot *= 40;
   }
   else if(type == "snowball")
   {
      o.rot *= 40;
      o.nrOfSnowballCollisions = 0;
   }
   else
   {
      o.rot *= 5;
   }
   o.dir = o.vx > 0 ? "right" : "left";
   o.p0 = {x:lx,y:ly};
   mc._x = lx;
   mc._y = ly;
   mc._rotation = getDeg(o);
   rhDecorateShot(o);
   initObject(o);
   resetNoColl();
   return o;
};

rhDecorateShot = function(o)
{
   if(o.aiShot == true)
   {
      o.rhTrailColor = 6697728;
      o.rhTrailW = 3;
      return undefined;
   }
   if(o.mega == true)
   {
      o.mc._xscale = o.mc._yscale = 175;
      o.mc.transform.colorTransform = new flash.geom.ColorTransform(1,0.55,0.5,1,90,0,0,0);
      o.mc.filters = [new flash.filters.GlowFilter(16724736,0.9,14,14,2,2)];
      o.r = 30;
      o.rhTrailColor = 16729122;
      o.rhTrailW = 7;
   }
   else if(o.type == "grenade")
   {
      o.mc.filters = [new flash.filters.GlowFilter(16763904,0.55,8,8,2,1)];
      o.rhTrailColor = 3355443;
      o.rhTrailW = 3;
   }
   else if(o.type == "rocket")
   {
      o.mc.filters = [new flash.filters.GlowFilter(16737792,0.7,10,10,2,1)];
      o.rhTrailColor = 16750899;
      o.rhTrailW = 4;
   }
   else
   {
      o.mc.filters = [new flash.filters.GlowFilter(16777215,0.7,8,8,2,1)];
      o.rhTrailColor = 16777215;
      o.rhTrailW = o.ammo == "triple" ? 3 : 5;
   }
};

rhShockwave = function(x, y, size, color)
{
   if(main.actionContainer == undefined)
   {
      return undefined;
   }
   var d = main.actionContainer.getNextHighestDepth();
   var s = main.actionContainer.createEmptyMovieClip("rhWave" + d,d);
   s._x = x;
   s._y = y;
   s.size = size;
   s.color = color == undefined ? 16777215 : color;
   s.t = 0;
   s.onEnterFrame = function()
   {
      this.t++;
      var r = this.size * (1 - Math.pow(0.82,this.t));
      this.clear();
      this.lineStyle(Math.max(1,9 - this.t * 0.6),this.color,Math.max(0,90 - this.t * 7));
      this.moveTo(r,0);
      var a = 0;
      while(a <= 24)
      {
         var an = a / 24 * 6.283185307179586;
         this.lineTo(Math.cos(an) * r,Math.sin(an) * r * 0.55);
         a++;
      }
      if(this.t > 14)
      {
         this.removeMovieClip();
      }
   };
};

// ------------------------------------------------------------- damage
rhDamageMul = function(obj)
{
   var D = rhD();
   if(obj.opponent == true)
   {
      return D.toEnemy / game.rhEnemyTough;
   }
   if(obj.penguin == true)
   {
      return D.toPlayer * _global.RH_ARMOR[rhClamp(rhNum(_global.saveProgress.armor),0,3)];
   }
   return 1;
};

// slow motion when the last enemy standing takes a knockout blow
rhAfterDamage = function(obj)
{
   if(obj.opponent != true || obj.rhKO == true || game.endOfGame == true)
   {
      return undefined;
   }
   if(obj.health - obj.hitpoints > 0)
   {
      return undefined;
   }
   obj.rhKO = true;
   rhPopup("K.O.!",obj.p0.x,obj.p0.y - 132,16729088,30);
   var left = 0;
   var i = 0;
   while(i < game.objects.length)
   {
      var o = game.objects[i];
      if(o.opponent == true && o.deceased != true && o.rhKO != true && o.health - o.hitpoints > 0)
      {
         left++;
      }
      i++;
   }
   if(left == 0)
   {
      game.rhSlow = 54;
   }
};

rhOnHeadshot = function(obj)
{
   game.rhBonus += 150;
   game.rhHeadshots++;
   rhPopup("HEADSHOT!",obj.p0.x,obj.p0.y - 95,16733440,26);
   rhPopup("+150",obj.p0.x,obj.p0.y - 68,16776960,16);
};

rhOnSplash = function(obj)
{
   if(obj.opponent == true && game.turn % 2 == 0)
   {
      game.rhBonus += 100;
      rhPopup("SPLASH! +100",obj.p1.x,game.raftLevel - 70,6750207,22);
   }
};

// --------------------------------------------------------- ammo slots
rhAmmoCount = function(n, rockNr)
{
   var p = level["player" + rockNr];
   if(n == 1)
   {
      return 999;
   }
   if(n == 2)
   {
      return rhNum(p.grenades);
   }
   if(n == 3)
   {
      return rhNum(p.rockets);
   }
   if(n == 4)
   {
      return rhNum(p.triples);
   }
   if(n == 5)
   {
      return rhNum(p.megas);
   }
   return 0;
};

// adds the two new ammo buttons next to the original three
rhSetupAmmoSlots = function(rockNr)
{
   var c = cannon;
   if(c.selectBall3 == undefined)
   {
      return undefined;
   }
   var dx = c.selectBall3._x - c.selectBall2._x;
   var n = 4;
   while(n <= 5)
   {
      var b = c.selectBall3.duplicateMovieClip("selectBall" + n,300 + n);
      b._x = c.selectBall3._x + dx * (n - 3);
      b._y = c.selectBall3._y;
      b.gotoAndStop(1);
      b.pic._visible = false;
      var ic = b.createEmptyMovieClip("rhIcon",50);
      if(n == 4)
      {
         var k = 0;
         while(k < 3)
         {
            var s = ic.attachMovie("mcSnowball","s" + k,k);
            s._xscale = s._yscale = 52;
            s._x = 15 + k * 12;
            s._y = 30 - (k == 1 ? 9 : 0);
            k++;
         }
      }
      else
      {
         var g = ic.attachMovie("mcGrenade","g",1);
         g._xscale = g._yscale = 125;
         g._x = 27;
         g._y = 26;
         g.transform.colorTransform = new flash.geom.ColorTransform(1,0.55,0.5,1,90,0,0,0);
         g.filters = [new flash.filters.GlowFilter(16724736,0.8,8,8,2,1)];
      }
      var cnt = rhAmmoCount(n,rockNr);
      var t = rhText(c,"rhCount" + n,320 + n,b._x + 2,b._y + 37,50,18,String(cnt),11,13056,"right","Arial");
      b.slot = n;
      if(cnt <= 0)
      {
         b._alpha = 35;
      }
      else
      {
         b.onRelease = function()
         {
            rhSelectAmmo(this.slot);
         };
      }
      n++;
   }
   selectBall(game.ballSelected);
};

rhSelectAmmo = function(n)
{
   if(cannon == undefined || cannon._name == undefined || game.instructionsDone != true)
   {
      return undefined;
   }
   var rockNr = game.fire.rockNr;
   if(rockNr == undefined || rhAmmoCount(n,rockNr) <= 0)
   {
      return undefined;
   }
   selectBall(n);
   game.ballSelected = n;
   game.ammoChosen = _global.RH_AMMO[n];
   rhDrawPreview();
};

// true when the point is over one of the Rehauled HUD buttons (no firing)
rhOverHud = function(x, y)
{
   if(cannon.selectBall4.hitTest(x,y,false) || cannon.selectBall5.hitTest(x,y,false))
   {
      return true;
   }
   if(hud.rhHud.wind.hitTest(x,y,false))
   {
      return true;
   }
   return false;
};

// ---------------------------------------------------------- aim scope
rhDrawPreview = function()
{
   var pv = hud.rhHud.preview;
   if(pv == undefined)
   {
      return undefined;
   }
   pv.clear();
   var lv = rhClamp(rhNum(_global.saveProgress.scope),0,3);
   if(lv <= 0 || game.instructionsDone != true || game.dontShoot == true || hud.mcKeu == undefined)
   {
      return undefined;
   }
   var bz = game.fire.schietMannetje.mc.bazooka;
   if(bz.loopPoint == undefined)
   {
      return undefined;
   }
   var ph = rhAmmoPhysics(game.ammoChosen);
   var rad = _global.cannonRotation * 0.017453292519943295;
   hitTestBounds(bz.loopPoint,main);
   var x = bz.loopPoint.xMin + Math.cos(rad) * 20;
   var y = bz.loopPoint.yMin + Math.sin(rad) * 20;
   var vx = _global.cannonPower * Math.cos(rad) / 3;
   var vy = _global.cannonPower * Math.sin(rad) / 3;
   var g = game.g * ph.m;
   var steps = _global.RH_SCOPE[lv];
   var i = 0;
   var ox = main._x;
   var oy = main._y;
   while(i < steps)
   {
      if(i > 0)
      {
         vx += game.rhWind;
      }
      vy += g;
      x += vx;
      y += vy;
      vx *= ph.airf;
      vy *= ph.airf;
      if(y > game.seaLevel + 10)
      {
         break;
      }
      if(i % 2 == 1)
      {
         var f = 1 - i / steps;
         pv.lineStyle();
         pv.beginFill(16777215,25 + f * 70);
         var r = 1.5 + f * 2;
         var sx = x + ox;
         var sy = y + oy;
         pv.moveTo(sx - r,sy);
         pv.curveTo(sx - r,sy - r,sx,sy - r);
         pv.curveTo(sx + r,sy - r,sx + r,sy);
         pv.curveTo(sx + r,sy + r,sx,sy + r);
         pv.curveTo(sx - r,sy + r,sx - r,sy);
         pv.endFill();
      }
      i++;
   }
};

rhClearPreview = function()
{
   hud.rhHud.preview.clear();
};
