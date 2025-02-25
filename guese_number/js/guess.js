function checkNumber(){
    const guess = document.getElementById('guess').value;
if (guess == random){
    document.getElementById('message').innerHTML="Correct";
}
else{
    document.getElementById('message').innerHTML="Wrong";
}
else if (guess < random) {
    message.innerHTML = "higher";  
} else {
    message.innerHTML = "lower";
}
}
