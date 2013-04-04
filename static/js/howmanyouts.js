"use strict";
var suits = {"c" : "club",
             "d" : "diamond",
             "h" : "heart",
             "s" : "spade"};


var gameEnded = false;
var rounds = [];
var stakeInterval = -1;
var nameTimeout = -1;

function addCommas(nStr)
{
    nStr += '';
    
    var x = nStr.split('.');    
    var x1 = x[0];
    var x2 = x.length > 1 ? '.' + x[1] : '';

    var rgx = /(\d+)(\d{3})/;
    while (rgx.test(x1)) {
        x1 = x1.replace(rgx, '$1' + ',' + '$2');
    }

    return x1 + x2;
}

function getCardRank(card) {

    return card.substr(0, card.length - 1);
} //end getCardRank

function getCardSuit(card) {

    return suits[card.substr(card.length - 1, 1)];
} //end getCardSuit

function gameStart() {

    // disable guess buttons until round is displayed
    disableGuess();

    // re-init everything
    $('#game-table').removeClass("game-over");
    $('#game-over').hide();
    $('#game-review').hide();
    $('#game-hiscores').show();

    rounds = [];
    gameEnded = false;
    
    clearInterval(stakeInterval);
    stakeInterval = -1;

    clearTimeout(nameTimeout);
    nameTimeout = -1;

    $('#game-score-number').html(0);
    $('#game-stake-number').html(0);

    $('#game-history .entry').removeClass("guess-history-wrong guess-history-close guess-history-perfect guess-history-pass");
    $('#game-history .entry').addClass("guess-history-pending");

    // make request to start    
    $.ajax({
        url: '/game/new',
        dataType: 'json',
        success: playRound,
        type: 'GET'
    });


} //end gameStart


function gameGuess(outs) {

    // bye bye start arrow
    $('#game-arrow').fadeOut(800);

    // disable guess buttons until round is displayed
    disableGuess();

    // hide hi scores
    $('#game-hiscores').hide();    

    // make a guess if the game is not over
    if (false === gameEnded) {

        clearInterval(stakeInterval);
        stakeInterval = -1;

        $.ajax({
            url: '/game/guess/' + encodeURIComponent(outs),
            dataType: 'json',
            success: playFeedback,
            type: 'POST'
        });
    }

} //end gameGuess

function gameRound(outs) {

    // place all the cards face down
    clearCards();

    // clear feedback
    clearFeedback();

    // grab new round if game is not over
    if (false === gameEnded) {

        clearInterval(stakeInterval);
        stakeInterval = -1;

        $.ajax({
            url: '/game/round',
            dataType: 'json',
            success: playRound,
            type: 'GET'
        });
    }

} //end gameRound

function gameName(name) {
    
    name = $.trim(name);    
    if (0 < name.length) {

        $.ajax({
            url: '/game/name/' + encodeURIComponent(name),
            dataType: 'json',
            type: 'POST'
        });

    }


} // end gameName



function playRound(data) {

    // store the new round for later use
    var round = data.game.round;
    rounds[data.game.round.id] = round;

    // at stake countdown
    clearInterval(stakeInterval);
    stakeInterval = -1;

    var stakeTotal = data.game.time * 1000;
    var stakeLeft  = stakeTotal;    
    var stakeCountdown = function () {
        
        stakeLeft  = stakeLeft - 100;

        if (0 > stakeLeft) {
            stakeLeft = 0;
            clearInterval(stakeInterval);        
        }

        var stake = Math.round(round.points * (stakeLeft / stakeTotal));
        $('#game-stake-number').html(stake);

    };

    // show the round and start the countdown past the first round
    displayRound(data.game.round);
    enableGuess();

    if (1 < data.game.round.id ) {
        stakeInterval = setInterval(stakeCountdown, 100);
    }

    // update hi scores
    $('#game-hiscores .game-hiscores-all-score').html(addCommas(data.game.alltime_score));
    $('#game-hiscores .game-hiscores-all-name').html(data.game.alltime_name);
    $('#game-hiscores .game-hiscores-interval-score').html(addCommas(data.game.interval_score));
    $('#game-hiscores .game-hiscores-interval-name').html(data.game.interval_name);

    
} //end playRound

function playFeedback(data) {

    if (data.game.feedback) {
     
        // store feedback for later use   
        rounds[data.game.feedback.id].feedback = data.game.feedback;

        // show the feedback for last guess
        displayFeedback(data.game.feedback);

        // if there is another hand to display, show the 'next round' button
        // otherwise end the game
        if ("yes" === data.game.more) {

            $('#game-next-round').show();    

        } else {

            clearInterval(stakeInterval);        
            gameEnded = true;
            
            // mark game over
            $('#game-table').addClass("game-over");
            $('#game-over').show();

            // fill in scores
            $('#game-over .game-over-score').html(addCommas(data.game.feedback.score));
            $('#game-over .game-over-rank-interval').html('#' + addCommas(data.game.feedback.rank_interval));
            $('#game-over .game-over-rank').html(addCommas('#' + data.game.feedback.rank));            
            $('#game-over .game-over-name').attr('value', data.game.name);            

            // generate twitter link
            var twitter = "http://twitter.com/share";
            var url = encodeURIComponent("http://howmanyouts.com");
            var text = encodeURIComponent("I just scored " + addCommas(data.game.feedback.score) + " points (ranks #" + data.game.feedback.rank_interval + " this week) on the poker game How Many Outs! Can you beat me? #howmanyouts");
            var href = twitter + "?url=" + url + "&text=" + text;

            $('#game-over .game-over-twitter').attr('href', href);


        }

    } 
    

} //end playRound


function reviewRound(roundId) {
    

    if (gameEnded && rounds[roundId]) {

        var round = rounds[roundId];        
        var feedback = rounds[roundId].feedback;
        
        // highligh hand being reviewed        
        var entry = '.entry' + (roundId);
        $('#game-history .entry .current').removeClass('selected');
        $('#game-history ' + entry + ' .current').addClass("selected");    

        // display round and feedback
        displayRound(round);
        displayFeedback(feedback);

    }


} //end reviewRound



function displayRound(round) {

    // place all the cards face down
    clearCards();

    // clear feedback
    clearFeedback();
        
    // display all the new cards
    displayCards(round);

    // points at stake
    var atStake = round.points;
    $('#game-stake-number').html(atStake);

    // highlight current hand history entry
    var entry = '.entry' + (round.id);
    $('#game-history .entry .current').removeClass('selected');
    $('#game-history ' + entry + ' .current').addClass("selected");    
         
    // place the status
    var status = "???";
    var statusClass = "unknown";
    var statusText = "";
    if (1 == round.ahead) {

        status = "ahead";
        statusClass = "ahead";
        statusText = "How many ways can you <span style='color:#FF0000'>lose</span>?";
    } else if (0 == round.ahead) {

        status = "tied";
        statusClass = "tied";
        statusText = "How many ways can you <span style='color:#FF0000'>lose</span>?";
    } else if (-1 == round.ahead) {
        
        status = "behind";
        statusClass = "behind";
        statusText = "How many ways can you <span style='color:#00DD00'>win</span>?";        
    }                   

    $('#game-status .top').html("You are <span class='" + statusClass + "'>" + status + "</span>");
    $('#game-status .bottom').html(statusText);        


} //end displayRound

function displayFeedback(feedback) {

    // show points earned
    $('#game-stake-number').html(feedback.points);    
    $('#game-score-number').html(feedback.score);    

    // figure out how close we were to the correct answer 
    var correctness = "wrong";
    switch(feedback.distance) {
            
        case 0:            
            correctness = "perfect";    
            break;
        case -1:
        case -2:
        case 1:
        case 2:
            correctness = "close";
            break;
        default:  
            correctness = "wrong";      
            break;
    }

    // highlight correctness
    $('#game-correctness').html(correctness + "!");
    $('#game-correctness').addClass("guess-" + correctness);    

    // highlight history 
    var entry = '.entry' + (feedback.id);
    $('#game-history ' + entry).removeClass("guess-history-pending");    
    $('#game-history ' + entry).addClass("guess-history-" + correctness);    

    // highlight guess buttons -- if the guess was not perfect, highlight the
    // correct answer as well
    var guessedButton = '.guess-button' + (feedback.guess);
    $('#game-controls ' + guessedButton).removeClass("guess-button-pending");        
    $('#game ' + guessedButton).addClass("guess-button-" + correctness);    

    if ("perfect" != correctness) {

        var outsCount = feedback.outs.length;
        if (outsCount >= 15) {
            outsCount = 15;
        }
        
        var correctButton = '.guess-button' + (outsCount);
        $('#game ' + correctButton).addClass("guess-button-perfect");    
    }
    

    // display outs
    displayOuts(feedback);

} //end displayFeedback

function displayOuts(feedback) {

            
    // clear any outs listed
    $('#game-review').hide();
    $('#game-outs-count').html('');
    $('#game-outs').html('');

    // display outs
    var xStart = 0;
    var xInterval = 30;      
    var xStop = 300;  
    var x = xStart;     

    var yStart = 33;
    var yInterval = 45;   
    var y = yStart;
    
    for (var i = 0; i < feedback.outs.length; ++i) {

       var rank = getCardRank(feedback.outs[i]);
       var suit = getCardSuit(feedback.outs[i]);
        
       $('#game-outs').append('<div style="left:' + x + 'px; top:' + y + 'px;" class="card ' + suit + '"><span>' + rank + '</span></div>');
                  
       // wrap around
        x = x + xInterval;           
       if (x >= xStop && (i + 1 < feedback.outs.length)) {
           x = xStart;
           y = y + yInterval;
       }

    }

    // display outs count and next round button
    var buttonY = y + yInterval + 5;
    var buttonX = 70;
    
    var msg = "NONE&nbsp;&nbsp;(0%)";    
    if (0 < feedback.outs.length) {

        var percent = Math.floor(feedback.outs.length / feedback.draws * 100);
        msg = feedback.outs.length + "&nbsp;&nbsp;(" + percent + "%)";

    } else {
        
        buttonY = 34;
        buttonX = 0;

    }


    // place next round button
    $('#game-next-round').css('top', buttonY);
    $('#game-next-round').css('left', buttonX);



    $('#game-outs-count').html(msg);             


    // flip
    $('#game-review').show();


} //end displayOuts


function displayCards(round) {
    
    // place the board cards
    var board = round.board;
    for (var i = 0; i < board.length; ++i) {

        var rank = getCardRank(board[i]);
        var suit = getCardSuit(board[i]);

        $('#game-board .card' + (i + 1)).html('<span>' + rank + '</span')
                                   .removeClass("down")
                                   .addClass(suit);
    }

    var hands = []
    for (var i = 0; i < round.hands.length; ++i) {
        hands[i] = round.hands[i];
    }

    // place the player cards
    for (var i = 0; i < hands[0].length; ++i) {

        rank = getCardRank(hands[0][i]);
        suit = getCardSuit(hands[0][i]);

        $('#game-hand-player .card' + (i + 1)).html('<span>' + rank + '</span')
                                        .removeClass("down")
                                        .addClass(suit);
    }

    // place the opponent cards
    for (var i = 1; i < hands.length; ++i) {
        for (var j = 0; j < hands[i].length; ++j) {

           rank = getCardRank(hands[i][j]);
           suit = getCardSuit(hands[i][j]);

           $('#game-hand-opp' + i + " .card" + (j + 1)).html('<span>' + rank + '</span')
                                                  .removeClass("down")
                                                  .addClass(suit);
        }
    }


} //end displayCards

function disableGuess() {

    $('#game-controls .guess-button').attr('disabled', 'disabled');

} //end disableGuess


function enableGuess() {

    $('#game-controls .guess-button').removeAttr('disabled');
    
} //end enableGuess
 

function clearCards() {
    
    $('.card').addClass('down')
              .removeClass('club diamond heart spade')
              .html('');


} //end clearCards

function clearFeedback() {

    $('#game-review').hide();
    $('#game-next-round').hide();    
        
    $('.guess-button').removeClass('guess-button-close guess-button-perfect guess-button-wrong');
    $('.guess-button').addClass('guess-button-pending');    

    $('#game-correctness').html('');
    $('#game-correctness').removeClass('guess-close guess-perfect guess-wrong');


} ///end clearFeedback


function changeName() {
    
    clearTimeout(nameTimeout);
    nameTimeout = -1;

    nameTimeout = setTimeout("gameName($('#game-over .game-over-name').attr('value'));", 500);


} //end changeName
 
function refreshHiScores() {
    

    $.ajax({
        url: '/scores/all',
        dataType: 'json',
        success: displayHiScores,
        type: 'GET'
    });

    $.ajax({
        url: '/scores/interval',
        dataType: 'json',
        success: displayHiScores,
        type: 'GET'
    });


} //end refreshHiScores

function displayHiScores(data) {
    

    if ("ok" === data.game.status) {
        
        var div = "hiscores-list-" + data.game.interval;
        for (var i = 0; i < data.game.scores.length; i++) {
            
            $("#" + div).append("<li><span class='hiscore-score'>" + addCommas(data.game.scores[i][2]) + "</span> <span class='hiscore-name'>" + data.game.scores[i][1]  + "</span></li>");

        }

    }


} //end displayHiScores
 

