// =====================================================================
//  Rehauled UI helpers: comic-style text, buttons, panels, popups.
//  Uses the fonts already embedded in the game ("CCThrills" is the
//  chunky comic font of the original titles).
// =====================================================================
_global.RH_FONT = "CCThrills";

rhFormat = function(size, color, align, font)
{
   var f = new TextFormat();
   f.font = font == undefined ? _global.RH_FONT : font;
   f.size = size;
   f.color = color;
   f.bold = f.font == "CCThrills";
   f.align = align == undefined ? "left" : align;
   return f;
};

rhText = function(mc, name, depth, x, y, w, h, txt, size, color, align, font)
{
   mc.createTextField(name,depth,x,y,w,h);
   var t = mc[name];
   t.embedFonts = true;
   t.selectable = false;
   t.multiline = true;
   t.wordWrap = true;
   t.setNewTextFormat(rhFormat(size,color,align,font));
   t.text = txt;
   return t;
};

// black comic outline + soft drop shadow
rhOutline = function(mc, thick, color)
{
   if(thick == undefined)
   {
      thick = 3;
   }
   if(color == undefined)
   {
      color = 0;
   }
   mc.filters = [new flash.filters.GlowFilter(color,1,thick,thick,12,1),new flash.filters.DropShadowFilter(2,60,0,0.45,3,3,1,1)];
};

rhRect = function(mc, x, y, w, h, r, fill, alpha, line, lineAlpha)
{
   if(line != undefined)
   {
      mc.lineStyle(3,line,lineAlpha == undefined ? 100 : lineAlpha);
   }
   else
   {
      mc.lineStyle();
   }
   mc.beginFill(fill,alpha);
   mc.moveTo(x + r,y);
   mc.lineTo(x + w - r,y);
   mc.curveTo(x + w,y,x + w,y + r);
   mc.lineTo(x + w,y + h - r);
   mc.curveTo(x + w,y + h,x + w - r,y + h);
   mc.lineTo(x + r,y + h);
   mc.curveTo(x,y + h,x,y + h - r);
   mc.lineTo(x,y + r);
   mc.curveTo(x,y,x + r,y);
   mc.endFill();
};

// Orange pill button, matching the original "DONE"/"BUY" buttons.
rhButton = function(parent, name, depth, x, y, w, h, label, size, onClick)
{
   var b = parent.createEmptyMovieClip(name,depth);
   b._x = x;
   b._y = y;
   b.bg = b.createEmptyMovieClip("bg",1);
   b.w = w;
   b.h = h;
   b.drawState = function(over)
   {
      this.bg.clear();
      rhRect(this.bg,0,0,this.w,this.h,this.h / 2,over ? 16757575 : 16747036,100,16777215,100);
      rhRect(this.bg,4,3,this.w - 8,this.h / 2 - 3,this.h / 4,16777215,over ? 30 : 22);
   };
   b.drawState(false);
   b.label = rhText(b,"label",2,0,(h - size * 1.25) / 2 - 1,w,size * 1.6,label,size,16776960,"center");
   rhOutline(b.label,3);
   b.onRollOver = function()
   {
      this.drawState(true);
   };
   b.onRollOut = b.onReleaseOutside = function()
   {
      this.drawState(false);
   };
   b.onRelease = onClick;
   b.filters = [new flash.filters.DropShadowFilter(3,60,0,0.4,4,4,1,1)];
   return b;
};

// Big outlined menu word (like PLAY / SCORES on the title screen).
rhMenuWord = function(parent, name, depth, x, y, label, size, onClick)
{
   var b = parent.createEmptyMovieClip(name,depth);
   b._x = x;
   b._y = y;
   var w = Math.round(label.length * size * 0.72) + 20;
   var hit = b.createEmptyMovieClip("hit",1);
   rhRect(hit,- w,0,w,size * 1.3,4,16777215,0);
   b.txt = b.createEmptyMovieClip("txt",2);
   var t = rhText(b.txt,"t",1,- w,0,w,size * 1.6,label,size,1118481,"right");
   b.txt.filters = [new flash.filters.GlowFilter(16775840,1,5,5,10,1),new flash.filters.GlowFilter(0,1,8,8,3,1),new flash.filters.DropShadowFilter(3,60,0,0.4,4,4,1,1)];
   b.onRollOver = function()
   {
      this._xscale = this._yscale = 108;
   };
   b.onRollOut = b.onReleaseOutside = function()
   {
      this._xscale = this._yscale = 100;
   };
   b.onRelease = onClick;
   return b;
};

// Full-screen modal: dim layer + panel. Returns the panel clip.
rhModal = function(name, depth, w, h, title)
{
   _root[name].removeMovieClip();
   var m = _root.createEmptyMovieClip(name,depth);
   var dim = m.createEmptyMovieClip("dim",1);
   dim.beginFill(0,55);
   dim.moveTo(0,0);
   dim.lineTo(640,0);
   dim.lineTo(640,480);
   dim.lineTo(0,480);
   dim.endFill();
   dim.useHandCursor = false;
   dim.onRelease = function()
   {
   };
   var p = m.createEmptyMovieClip("panel",2);
   p._x = Math.round((640 - w) / 2);
   p._y = Math.round((480 - h) / 2);
   rhRect(p,0,0,w,h,18,16764736,100,16777215,100);
   rhRect(p,8,8,w - 16,h - 16,12,16772245,100);
   p.filters = [new flash.filters.DropShadowFilter(6,60,0,0.5,10,10,1,2)];
   if(title != undefined)
   {
      var t = rhText(p,"title",10,0,12,w,48,title,30,16776960,"center");
      rhOutline(t,4);
   }
   p.w = w;
   p.h = h;
   return p;
};

// Floating combat text in world coordinates (lives in main.actionContainer).
rhPopup = function(txt, x, y, color, size)
{
   if(main.actionContainer == undefined)
   {
      return undefined;
   }
   if(size == undefined)
   {
      size = 22;
   }
   var d = main.actionContainer.getNextHighestDepth();
   var c = main.actionContainer.createEmptyMovieClip("rhPop" + d,d);
   var t = rhText(c,"t",1,-150,0,300,size * 1.6,txt,size,color,"center");
   rhOutline(t,4);
   c._x = x;
   c._y = y;
   c._xscale = c._yscale = 40;
   c.tel = 0;
   c.onEnterFrame = function()
   {
      this.tel++;
      if(this.tel < 8)
      {
         this._xscale = this._yscale = 40 + this.tel * 10;
      }
      else if(this.tel < 10)
      {
         this._xscale = this._yscale = 120 - (this.tel - 8) * 10;
      }
      this._y -= 1.2;
      if(this.tel > 40)
      {
         this._alpha -= 6;
         if(this._alpha <= 0)
         {
            this.removeMovieClip();
         }
      }
   };
   return c;
};

// Same, but in screen space on the HUD.
rhBanner = function(txt, y, color, size, hold)
{
   if(hud == undefined)
   {
      return undefined;
   }
   var d = hud.getNextHighestDepth();
   var c = hud.createEmptyMovieClip("rhBan" + d,d);
   var t = rhText(c,"t",1,-320,0,640,size * 1.6,txt,size,color,"center");
   rhOutline(t,5);
   c._x = 320;
   c._y = y;
   c.tel = 0;
   c.hold = hold == undefined ? 50 : hold;
   c._xscale = c._yscale = 30;
   c.onEnterFrame = function()
   {
      this.tel++;
      if(this.tel < 8)
      {
         this._xscale = this._yscale = 30 + this.tel * 11;
      }
      else if(this.tel < 11)
      {
         this._xscale = this._yscale = 118 - (this.tel - 8) * 6;
      }
      if(this.tel > this.hold)
      {
         this._alpha -= 8;
         if(this._alpha <= 0)
         {
            this.removeMovieClip();
         }
      }
   };
   return c;
};
