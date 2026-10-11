// =====================================================================
//  Local high scores (the original BubbleBox score server is gone).
//  Stored in the same SharedObject as the save game.
// =====================================================================
rhRunLabel = function()
{
   var d = rhD().name;
   if(rhIsEndless())
   {
      return "ENDLESS W" + _global.RH.wave + " " + d;
   }
   var lv = Math.min(11,_global.progress.level);
   return "LEVEL " + lv + " " + d;
};

rhAddScore = function(name, score, label)
{
   var so = rhSO();
   if(so.data.scores == undefined)
   {
      so.data.scores = [];
   }
   var list = so.data.scores;
   var entry = {n:name,s:Math.round(score),l:label,t:new Date().getTime()};
   list.push(entry);
   list.sortOn("s",Array.DESCENDING | Array.NUMERIC);
   while(list.length > 10)
   {
      list.pop();
   }
   so.data.lastName = name;
   so.flush();
   var i = 0;
   while(i < list.length)
   {
      if(list[i].t == entry.t && list[i].n == name && list[i].s == entry.s)
      {
         return i + 1;
      }
      i++;
   }
   return 0;
};

rhShowScores = function(highlight, onClose)
{
   var p = rhModal("rhModalMC",900,460,380,"HIGH SCORES");
   var list = rhSO().data.scores;
   if(list == undefined || list.length == 0)
   {
      rhText(p,"empty",11,20,150,420,60,"No scores yet.\nBeat the campaign or survive some endless waves!",15,6697728,"center");
   }
   else
   {
      var i = 0;
      while(i < list.length && i < 10)
      {
         var e = list[i];
         var col = i + 1 == highlight ? 13369344 : 6697728;
         var y = 62 + i * 25;
         rhText(p,"r" + i,20 + i * 4,26,y,40,24,(i + 1) + ".",15,col,"right");
         rhText(p,"n" + i,21 + i * 4,74,y,150,24,e.n,15,col,"left");
         rhText(p,"l" + i,22 + i * 4,214,y + 3,130,24,e.l == undefined ? "" : e.l,10,col,"left");
         rhText(p,"s" + i,23 + i * 4,330,y,104,24,String(e.s),15,col,"right");
         i++;
      }
   }
   var b = rhButton(p,"close",90,160,326,140,36,"OK",18,function()
   {
      var cb = this.onClose;
      _root.rhModalMC.removeMovieClip();
      if(cb != undefined)
      {
         cb();
      }
   });
   b.onClose = onClose;
};

rhEnterScore = function(score, label, onDone)
{
   score = Math.round(rhNum(score));
   var p = rhModal("rhModalMC",900,420,250,"YOUR SCORE");
   var s = rhText(p,"score",11,0,56,420,50,String(score),36,16776960,"center");
   rhOutline(s,4);
   rhText(p,"lbl",12,0,108,420,24,(label == undefined ? "" : label + "  -  ") + "enter your name:",13,6697728,"center");
   var box = p.createEmptyMovieClip("box",13);
   rhRect(box,90,134,240,38,10,16777215,100,6697728,100);
   p.createTextField("nameField",14,98,138,224,32);
   var nf = p.nameField;
   nf.type = "input";
   nf.embedFonts = true;
   nf.maxChars = 12;
   nf.restrict = "A-Za-z0-9 \\-_!.";
   nf.setNewTextFormat(rhFormat(20,3355443,"center"));
   var last = rhSO().data.lastName;
   nf.text = last == undefined ? "SIMON" : last;
   Selection.setFocus(nf);
   Selection.setSelection(0,nf.text.length);
   var ok = rhButton(p,"ok",20,140,190,140,40,"SAVE",20,function()
   {
      var pp = this._parent;
      var nm = pp.nameField.text;
      if(nm == "" || nm == undefined)
      {
         nm = "???";
      }
      var rank = rhAddScore(nm.toUpperCase(),pp.score0,pp.label0);
      rhShowScores(rank,pp.onDone0);
   });
   p.score0 = score;
   p.label0 = label;
   p.onDone0 = onDone;
};

// The original code calls this for its online score panel; route it locally.
_global.startHighscores = function(clip, score)
{
   clip._visible = false;
   rhEnterScore(score,rhRunLabel());
};

// score of the current run (endless runs also get 1000 per cleared wave)
rhRunScore = function()
{
   var pts = rhNum(_global.progress.points);
   if(rhIsEndless())
   {
      pts += (_global.RH.wave - 1) * 1000;
   }
   return Math.round(pts * rhD().scoreMul);
};

rhEndlessGameOver = function()
{
   var D = rhD();
   var sc = rhRunScore();
   _global.rhPendingScore = {score:sc,label:"ENDLESS W" + _global.RH.wave + " " + D.name};
   rhClearSave();
   _global.inGame = false;
};
