// =====================================================================
//  DEBUG BUILD ONLY (DEBUG=1 ./build.sh): lets the Playwright test
//  harness drive the game through ExternalInterface.
//    player.rh("get", "_global.progress.level")
//    player.rh("set", "_global.saveProgress.money", 5000)
//    player.rh("call", "rhShowScores", [])
//    player.rh("goto", "overview")
// =====================================================================
rhDebugCmd = function(cmd, a, b)
{
   if(cmd == "get")
   {
      return String(eval(a));
   }
   if(cmd == "set")
   {
      set(a,b);
      return "ok";
   }
   if(cmd == "call")
   {
      var f = eval(a);
      if(typeof f != "function")
      {
         return "nofunc " + a;
      }
      var r = f.apply(_root,b == undefined ? [] : b);
      return String(r);
   }
   if(cmd == "goto")
   {
      _root.mcControlCenter.removeMovieClip();
      _root.gotoAndStop(a);
      return "ok";
   }
   if(cmd == "state")
   {
      var s = "frame=" + _root._currentframe + " turn=" + game.turn + " wind=" + game.rhWind + " balls=" + game.cannonBalls.length + " end=" + game.endOfGame + " winner=" + game.winner;
      var i = 0;
      while(i < game.objects.length)
      {
         var o = game.objects[i];
         s += "\n obj" + i + " opp=" + o.opponent + " hp=" + o.health + " pend=" + o.hitpoints + " x=" + Math.round(o.p0.x) + " y=" + Math.round(o.p0.y) + " dead=" + o.deceased;
         i++;
      }
      i = 0;
      while(i < game.cannonBalls.length)
      {
         var c = game.cannonBalls[i];
         s += "\n ball" + i + " type=" + c.type + " ammo=" + c.ammo + " x=" + Math.round(c.p0.x) + " y=" + Math.round(c.p0.y) + " vx=" + c.vx + " vy=" + c.vy + " mc=" + c.mc + " follow=" + (cannonBallToFollow == c);
         i++;
      }
      s += "\n scroll=" + scrollPos + " follow=" + cannonBallToFollow.type + " callTurn=" + callTurnScroll + " power=" + _global.cannonPower + " rot=" + _global.cannonRotation;
      if(game.rhLastAI != undefined)
      {
         s += "\n lastAI target=" + Math.round(game.rhLastAI.target) + " ideal=" + game.rhLastAI.ideal + " power=" + game.rhLastAI.power + " err=" + game.rhLastAI.err;
      }
      return s;
   }
   return "unknown";
};
flash.external.ExternalInterface.addCallback("rh",null,rhDebugCmd);

// fire the player's shot at enemy #idx (index among living enemies) with the given ammo slot
rhDbgFire = function(slot, idx, dy)
{
   if(cannon == undefined || cannon._name == undefined)
   {
      return "not ready";
   }
   rhSelectAmmo(slot);
   var foes = rhLivingCrew(2);
   var t = foes[idx == undefined ? 0 : idx];
   if(t == undefined)
   {
      return "no target";
   }
   var ph = rhAmmoPhysics(game.ammoChosen);
   var rotDeg = -38;
   _global.cannonRotation = rotDeg;
   var bz = game.fire.schietMannetje.mc.bazooka;
   bz._rotation = 180 + rotDeg;
   var rad = rotDeg * 0.017453292519943295;
   hitTestBounds(bz.loopPoint,main);
   var lx = bz.loopPoint.xMin + Math.cos(rad) * 20;
   var ly = bz.loopPoint.yMin + Math.sin(rad) * 20;
   var ty = t.p0.y - (dy == undefined ? 25 : dy);
   var lo = 4;
   var hi = 170;
   var i = 0;
   while(i < 24)
   {
      var mid = (lo + hi) / 2;
      var x = rhSimLand(lx,ly,mid * Math.cos(rad) / 3,mid * Math.sin(rad) / 3,ph.m,ph.airf,game.rhWind,ty,700);
      if(x == null || x < t.p0.x)
      {
         lo = mid;
      }
      else
      {
         hi = mid;
      }
      i++;
   }
   _global.cannonPower = (lo + hi) / 2;
   game.dontShoot = false;
   vuurSchot();
   Mouse.removeListener(_global.mouseListener);
   hud.mcKeu.removeMovieClip();
   return "fired power=" + _global.cannonPower + " at x=" + t.p0.x;
};
