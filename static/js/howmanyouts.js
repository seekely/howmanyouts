
var suits = {"c" : "club"
           , "d" : "diamond"
           , "h" : "heart"
           , "s" : "spade"};


var timerOn = 0;          
var timeLeft = 0;


var rounds = [];
var gameEnded = false;

function getCardRank(card) {

    return card.substr(0, card.length - 1);
    
} //end getCardRank

function getCardSuit(card) {

    return suits[card.substr(card.length - 1, 1)];
    
} //end getCardSuit

function gameStart() {

    rounds = [];
    ended = false;
    
    $.ajax({
        url: '/game/new',
        dataType: 'json',
        success: displayRound
    });


} //end gameStart


function gameGuess(outs) {

    if (false == gameEnded) {

        clearInterval(timerOn);
        timerOn = 0;

        $.ajax({
            url: '/game/guess/' + outs,
            dataType: 'json',
            success: displayRound
        });
    }

} //end gameGuess

function displayRound(data) {

    if (data.game.feedback) {
        displayFeedback(data);
    }

    // game stats
    $('#game_id').html(data.game.id);
    $('#score').html(data.game.score);
    $('#remaining').html(data.game.time);
    $('#streak').html(data.game.streak);

    // place all the cards face down
    clearCards();

    // if there is another round to play out
    if (data.game.round.new == "yes") {

        // store the round for history   
        rounds[data.game.round.id] = data.game.round;
        
        // display all the new cards
        displayCards(data.game.round);
        
        // place the status
        if (data.game.round.ahead) {
            $('#ahead').html("You are ahead.  How many ways can you lose?");
        } else {
            $('#ahead').html("You are behind.  How many ways can you win?");
        }

        // reset the slider
        $( "#slider-horizontal" ).slider( "value", 12)
        $( "#amount").val(12)

        // run  the timer
        timeLeft = data.game.round.time * 1000;
        if (0 < timeLeft) {
            clearInterval(timerOn);
            timerOn = setInterval("countdown()", 100);
        }

    } else {
        
        alert("THIS GAME BE DONE YO");
        gameEnded = true;

    }

} //end displayRound

function displayFeedback(data) {

    // store
    rounds[data.game.feedback.id].feedback = data.game.feedback;

    // hand history
    var add = "wrong";
    var entry = '.entry' + (data.game.feedback.id);
    $('#history ' + entry).removeClass("pending");    

    if (100 <= data.game.feedback.guess) {
        
        switch(data.game.feedback.guess) {
            
            case 100:
                add = "pass";
                break;
            default:
                add = "wrong";
                break;
        }

    } else {
        
        switch(data.game.feedback.distance) {
            
            case 0:            
                add = "perfect";    
                break;
            case -1:
            case -2:
            case 1:
            case 2:
                add = "close";
                break;
            default:  
                add = "wrong";      
                break;
        }
    }

    $('#history ' + entry).addClass(add);    


} //end displayFeedback


function clearCards() {
    
    $('.card').addClass('down')
              .removeClass('club diamond heart spade')
              .html('');

} //end clearCards


function displayCards(round) {
    
    // place the board cards
    board = round.board;
    for (var i = 0; i < board.length; ++i) {

        rank = getCardRank(board[i]);
        suit = getCardSuit(board[i]);

        $('#board .card' + (i + 1)).html('<span>' + rank + '</span')
                                   .removeClass("down")
                                   .addClass(suit);
    }

    hands = []
    for (var i = 0; i < round.hands.length; ++i) {
        hands[i] = round.hands[i];
    }

    // place the player cards
    for (var i = 0; i < hands[0].length; ++i) {

        rank = getCardRank(hands[0][i]);
        suit = getCardSuit(hands[0][i]);

        $('#player-hand .card' + (i + 1)).html('<span>' + rank + '</span')
                                        .removeClass("down")
                                        .addClass(suit);
    }

    // place the opponent cards
    for (var i = 1; i < hands.length; ++i) {
        for (var j = 0; j < hands[i].length; ++j) {

           rank = getCardRank(hands[i][j]);
           suit = getCardSuit(hands[i][j]);

           $('#opp-hand' + i + " .card" + (j + 1)).html('<span>' + rank + '</span')
                                                  .removeClass("down")
                                                  .addClass(suit);
        }
    }


} //end displayCards


function reviewHistory(id) {

    
    if (gameEnded && rounds[id]) {
        
        round = rounds[id];
        feedback = rounds[id].feedback;

        // clear any outs listed
        $('#review').html('');

        // place all the cards face down
        clearCards();
        
        // display cards on the board
        displayCards(round);

        // display outs
        for (var i = 0; i < feedback.outs.length; ++i) {

           rank = getCardRank(feedback.outs[i]);
           suit = getCardSuit(feedback.outs[i]);
            
           $('#review').append('<div class="card ' + suit + '"><span>' + rank + '</span></div>');

        }

    }

} //end reviewHistory

function countdown() {
    
    timeLeft = timeLeft - 100;

    var display = timeLeft / 1000;
    $('#time').html(display);

    // out of time? force a guess since server side will ignore any
    // real guess
    if (0 >= timeLeft) {
        gameGuess(101);        
    }
}





