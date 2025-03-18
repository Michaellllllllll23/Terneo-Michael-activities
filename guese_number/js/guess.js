function checkNumber(){
    const guess= parseInt(document.getElementById('guess').value);
    const message = document.getElementById('massage');
if (guess === random){
    message.innerHTML="Correct";
}else if (guess < random){
    message.innerHTML="higher";
} else {
    message.innerHTML = "lower";
}
}

