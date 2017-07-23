// For square displays of posts

// function to format post's text aesthetically by wrapping it
function textWrapper(theContext, text, x, y, len, rad) {
	// array of post's words split word-by-word
	var tokenized = text.split(' ');
	// initializes an empty "line" to start putting words into 
	var line = '';

	for(var n = 0; n < tokenized.length; n++) {
		// initialize temp, a line with the word added
		var temp = line + tokenized[n] + ' ';
		var measure = theContext.measureText(temp);
		var testWidth = measure.width;
		// if the temp line is longer than a wrapped line should be, output the line without the new word
		if (testWidth > 2*rad - 15 && n > 0) {
			theContext.fillText(line, x, y);
			// begins the new line to be next added (first word is current word)
			line = tokenized[n] + ' ';
			// adjusts the coordinate so the next line will be below the one just written
			y += 28;
		  }
		
		// otherwise, add the word to line and don't display it yet
		else {
			line = temp;
		  }
		}
		
		// displays last line that is not displayed via for-loop
		theContext.fillText(line, x, y);
	}
	
function SimpleSquareParticle(posX, posY, text, title, name, address, len, rad) {
		this.x = posX;
		this.y = posY;
		this.velX = 0;
		this.velY = 0;
		this.accelX = 0;
		this.accelY = 0;
		this.color = "#FF0000";
		this.radius = 200;
		this.text = text;
		this.title = title;
		this.name = name;
		this.address = address;
		this.len = len;
		this.rad = rad;
}

//The function below returns a Boolean value representing whether the point with the coordinates supplied "hits" the particle.
SimpleSquareParticle.prototype.hitTest = function(hitX,hitY) {
	return((hitX > this.x - this.rad)&&(hitX < this.x + this.rad)&&(hitY > this.y - this.rad)&&(hitY < this.y + this.rad));
}

//A function for drawing the particle.
SimpleSquareParticle.prototype.drawToContext = function(theContext) {
	theContext.fillStyle = this.color;
	theContext.fillRect(this.x - this.rad, this.y - this.rad, 2*this.rad, 2*this.rad);
	theContext.font = 18 + 10*(1 - this.len/500) + "px serif";
	theContext.fillStyle="white";
	// displays wrapped text of post 
	textWrapper(theContext, this.text, this.x - 0.9*this.rad, this.y - 0.55*this.rad + 0.5*this.rad*(1 - this.len/500), this.len, this.rad);
	theContext.font = "18px serif";
	// displays poster's email address
	theContext.fillText(this.address + "@college.harvard.edu", this.x - 0.6*this.rad, this.y - this.rad + 40 + 20*(this.len/500));
	theContext.font = "25px serif";
	// displays post's title of poster's name 
	theContext.fillText(this.title + " by " + this.name, this.x - this.rad, this.y - 0.85*this.rad);
	
}