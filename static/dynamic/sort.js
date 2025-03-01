var COLUMN = -1
var dir = 1

function sortResults(column){
    var table, sorted, rows, x, y, change;
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
            x = rows[i].cells[column].innerHTML;
            y = rows[i+1].cells[column].innerHTML;
            if (column==0 | column==2 | column==4){
                if((dir==1 && ((x.toLowerCase() > y.toLowerCase() && !(isNaN(x.substring(0,1)) && !isNaN(y.substring(0,1)))) || (!isNaN(x.substring(0,1)) && isNaN(y.substring(0,1))))) 
                    || (dir==-1 && ((x.toLowerCase() < y.toLowerCase() && !(isNaN(y.substring(0,1)) && !isNaN(x.substring(0,1)))) || (isNaN(x.substring(0,1)) && !isNaN(y.substring(0,1)))))){
                    rows[i].parentNode.insertBefore(rows[i+1],rows[i]);
                    sorted = false;
                }
            }
            if (column == 1){
                if (x*dir<y*dir){
                    rows[i].parentNode.insertBefore(rows[i+1],rows[i]);
                    sorted = false;
                }
            }
            if (column == 3){
                if (Number(x.substring(0,4))*dir < Number(y.substring(0,4))*dir){
                    rows[i].parentNode.insertBefore(rows[i+1],rows[i]);
                    sorted = false;
                }
            }
        }
    }
}