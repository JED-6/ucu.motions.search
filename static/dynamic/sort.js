var COLUMN = -1
var dir = 1

function replace_special(text){
    text = text.replaceAll("SPECIAL1","<br>");
    text = text.replaceAll("SPECIAL2","'");
    text = text.replaceAll("SPECIAL3",'"');
    return text;
}

function flattern_content(){
    for (var i=0;i<motions.length;i++){
        if(motions[i][3]){
            document.getElementById(motions[i][0]).innerHTML = motions[i][1];
            motions[i][3] = false;
        }
    }
}

function expand_content(id){
    var motion;
    for (var i=0;i<motions.length;i++){
        if(motions[i][0]==id && motions[i][3]){
            document.getElementById(motions[i][0]).innerHTML = motions[i][1];
            motions[i][3] = false;
            break;
        }
        else if(motions[i][0]==id){
            motion = motions[i][2];
            motion = motion.replaceAll(motions[i][1],'<span style="color:red;font-weight:bold;">'+motions[i][1]+"</span>")
            document.getElementById(id).innerHTML = motion;
            motions[i][3] = true;
        }
        else if(motions[i][3]){
            document.getElementById(motions[i][0]).innerHTML = motions[i][1];
            motions[i][3] = false;
        }
    }
}

function sortResults(column){
    var table, sorted, rows, x, y;
    flattern_content()
    if (COLUMN == column){
        dir = dir*-1;
    }
    COLUMN = column;

    table = document.getElementById("results_table");
    sorted = false;
    while(!sorted){
        sorted = true;
        rows = table.rows;
        for (i=1; i<(rows.length-1); i++){
            if (column == 3){
                x = rows[i].cells[column].children[0].innerHTML;
                y = rows[i+1].cells[column].children[0].innerHTML;
            }
            else{
                x = rows[i].cells[column].innerHTML;
                y = rows[i+1].cells[column].innerHTML;
            }
            if (column==1 | column==3 | column==5){
                if((dir==1 && ((x.toLowerCase() > y.toLowerCase() && !(isNaN(x.substring(0,1)) && !isNaN(y.substring(0,1)))) || (!isNaN(x.substring(0,1)) && isNaN(y.substring(0,1))))) 
                    || (dir==-1 && ((x.toLowerCase() < y.toLowerCase() && !(isNaN(y.substring(0,1)) && !isNaN(x.substring(0,1)))) || (isNaN(x.substring(0,1)) && !isNaN(y.substring(0,1)))))){
                    rows[i].parentNode.insertBefore(rows[i+1],rows[i]);
                    sorted = false;
                }
            }
            if (column == 2){
                if (x*dir<y*dir){
                    rows[i].parentNode.insertBefore(rows[i+1],rows[i]);
                    sorted = false;
                }
            }
            if (column == 4){
                if (Number(x.substring(0,4))*dir < Number(y.substring(0,4))*dir){
                    rows[i].parentNode.insertBefore(rows[i+1],rows[i]);
                    sorted = false;
                }
            }
        }
    }
}