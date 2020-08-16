function formatBytes(a, b) { 
    if (0 == a) return "0 Bytes"; 
    var c = 1024, d = b || 2, e = ["Bytes", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB"], f = Math.floor(Math.log(a) / Math.log(c)); 
    return parseFloat((a / Math.pow(c, f)).toFixed(d)).toFixed(b) + " " + e[f] 
}

function toHHMMSS(sec_num) {
    var hours   = Math.floor(sec_num / 3600);
    var minutes = Math.floor((sec_num - (hours * 3600)) / 60);
    var seconds = sec_num - (hours * 3600) - (minutes * 60);

    if (hours   < 10) {hours   = "0"+hours;}
    if (minutes < 10) {minutes = "0"+minutes;}
    if (seconds < 10) {seconds = "0"+seconds;}
    return hours+':'+minutes+':'+seconds;
}

$('select').material_select();
$('.modal').modal();
function openRoom(room_id) {
    $.get("/open?room_id=" + room_id, function (data) {
        Materialize.toast(data, 5000)
    })
}
function closeRoom(room_id) {
    $.get("/close?room_id=" + room_id, function (data) {
        Materialize.toast(data, 5000)
    })
}
function confirmCloseRoom(room_id) {
    $("#open_room_confirm_title").html("Confirmation")
    $("#open_room_confirm_content").html("Stop recording " + room_id + "?")
    $("#open_room_modal_buttons").html("<a href='#!' class='modal-action modal-close waves-effect waves-green btn-flat' onclick='closeRoom(" + room_id + ")'>Yes</a> \
            <a href='#!' class='modal-action modal-close waves-effect waves-green btn-flat'>No</a>")
    $('#open_room_modal').modal('open');
}
function load_config() {
    $.ajax({
        url: "/get_config",
        dataType: 'json',
        async: false,
        success: function (data) {
            $("#savepath").val(data['savepath'])
            $("#open_on_init").val(data['load_on_init'].join(","))
        }
    });
}
function save_config() {
    savepath = $("#savepath").val()
    open_on_init = $("#open_on_init").val().split(",")
    open_on_init = $.map(open_on_init, function (v) {
        var i = parseInt(v)
        if (isNaN(i)) {
            return -1
        } else {
            return i
        }
    })
    if (open_on_init.indexOf(-1) > -1) {
        Materialize.toast('Invalid room IDs!', 5000)
        return
    }
    json = JSON.stringify({
        "savepath": savepath,
        "load_on_init": open_on_init
    })
    $.get("/save_config?json=" + encodeURIComponent(json), function (data) {
        Materialize.toast(data, 5000)
    })
}
$("#open_room").click(function () {
    var room_id = $("#room_id").val()
    if (room_id) {
        $("#open_room_confirm_title").html("Confirmation")
        $("#open_room_confirm_content").html("Start recording " + room_id + "?")
        $("#open_room_modal_buttons").html("<a href='#!' class='modal-action modal-close waves-effect waves-green btn-flat' onclick='openRoom(" + room_id + ")'>Yes</a> \
                <a href='#!' class='modal-action modal-close waves-effect waves-green btn-flat'>No</a>")
    } else {
        $("#open_room_confirm_title").html("Error")
        $("#open_room_confirm_content").html("Please enter room ID.")
        $("#open_room_modal_buttons").html("<a href='#!' class='modal-action modal-close waves-effect waves-green btn-flat'>Okay</a>")
    }
    $("#open_room_modal").modal("open")
})
function getUserInfo(roomID) {
    $.get({
        type: "get",
        url: `/get_user_info?room_id=${roomID}`,
        dataType: 'json',
        async: true,
        success: function (data) {
            $("#room" + roomID + "_uname").html(data['info']['uname'])
            $("#room" + roomID + "_face").attr("src", data['info']['face'])
        }
    });
}
var hist = [];
const n_records = 10;
for (var i = 0; i < n_records; i++) {
    hist.push({
        "processes": [],
        "status": {},
        "time": Date.now() / 1000,
        "running": [],
        "waiting": []
    })
}
function update() {
    var processes = []
    var status = {}
    var response_time = 0;
    var html = ""

    $.ajax({
        url: "/info",
        dataType: 'json',
        async: true,
        success: function (data) {
            $.each(data["status"], function (key, val) {
                status[key] = {
                    "start_time": val["start_timestamp"],
                    "time": val["time"],
                    "downloaded_size": val["downloaded_size"],
                    "download_speed": val["download_speed"]
                }
            });
            processes = data["processes"];
            response_time = parseFloat(data["time"]);

            
            running_status = $.extend({}, status)
            $.each(processes, function (i, room_id) {
                if (room_id in status) {
                } else {
                    status[room_id] = {
                        "start_time": 0,
                        "time": 0,
                        "downloaded_size": 0,
                        "download_speed": 0
                    }
                }
            })

            running = []
            waiting = []
            $.each(processes, function (i, room_id) {
                if (status[room_id]["download_speed"] == 0) {
                    waiting[waiting.length] = room_id
                } else {
                    running[running.length] = room_id
                }
            })

            listHasNotChanged = (JSON.stringify(hist[hist.length - 1]["processes"]) == JSON.stringify(processes) && 
                                JSON.stringify(hist[hist.length - 1]["running"]) == JSON.stringify(running) &&
                                JSON.stringify(hist[hist.length - 1]["waiting"]) == JSON.stringify(waiting))
            $.each(running.concat(waiting), function (i, room_id) {
                info = status[room_id]
                total_downloaded_size = formatBytes(info["downloaded_size"], 4)
                download_speed = info["download_speed"]
                download_speed_string = "0 Bytes/s"
                duration = toHHMMSS(Math.floor((info["time"]) - parseFloat(info["start_time"])))
                if (room_id in hist[hist.length - 1]["status"]) {
                    for (var i = 0; i < n_records; i++) {
                        if (room_id in hist[i]["status"]) {
                            first_elem = hist[i];
                            break;
                        }
                    }
                    download_speed_float = (parseInt(info["downloaded_size"]) - parseInt(first_elem["status"][room_id]["downloaded_size"])) / (response_time - first_elem["time"])
                    download_speed_string = formatBytes(download_speed_float, 4) + "/s"
                    /*download_speed_instant = (parseInt(info["downloaded_size"]) - parseInt(hist[n_records - 1]["status"][room_id]["downloaded_size"])) / (response_time - hist[n_records - 1]["time"])
                    download_speed_instant_string = formatBytes(download_speed_instant, 4) + "/s"
                    download_speed_string += " (" + download_speed_instant_string + ")"*/
                } else {
                    download_speed_string = "- Bytes/s"
                }
                badge = download_speed == 0 ? "pending" : "recording"
                badge_color = download_speed == 0 ? "orange" : "green"
                content = `
                        <div class="collapsible-header">
                            <span class="new badge right middle ${badge_color}" data-badge-caption="${badge}"></span>
                            <ul class="collection">
                                <li class="collection-item avatar">
                                    <img src="https://static.hdslb.com/images/member/noface.gif" alt="" id="room${room_id}_face" class="circle">
                                    <span class="title">
                                        <b class="truncate" id="room${room_id}_uname">
                                            哔哩哔哩 - ( ゜- ゜)つロ 乾杯~
                                        </b>
                                    </span>
                                    <p>
                                        <h class="truncate">Room ID: ${room_id}</h>
                                        <h id='room${room_id}_total_download'>${total_downloaded_size}</h>
                                    </p>
                                </li>
                            </ul>
                        </div>
                        <div class="collapsible-body">
                            <div class="row">
                                <div class="col s12">
                                    Download Speed: <h id='room${room_id}_download_speed'>${download_speed_string}</h>
                                    <br>
                                    Duration: <h id='room${room_id}_duration'>${duration}</h>
                                </div>
                                <div class="col s12">
                                ${processes.indexOf(room_id) > -1 ? `<a href='#!' class='waves-effect waves-light btn right red' onclick='confirmCloseRoom(${room_id})'><i class='material-icons left'>close</i>STOP</a>` : ""}
                                </div>
                            </div>
                        </div>
                        `
                if (listHasNotChanged) { // no new tasks
                    // $("#room" + room_id).html(content)
                    $("#room" + room_id + "_total_download").html(total_downloaded_size)
                    $("#room" + room_id + "_download_speed").html(download_speed_string)
                    $("#room" + room_id + "_duration").html(duration)
                } else {
                    html += `<li class='collection-item' id='room${room_id}'>${content}</li>`
                }
            })
            if (html != "") {
                $("#tasks").html(html)
                $.each(processes, function(i, room_id) {
                    getUserInfo(room_id)
                })
            }

            hist.push({
                "processes": processes,
                "status": status,
                "time": response_time,
                "running": running,
                "waiting": waiting
            })
            hist.shift()
        }
    });
}
setInterval(update, 1000)
update() // update manually once
$.get({
    type: "get",
    url: `/get_disk_usage`,
    dataType: 'json',
    async: true,
    success: function (data) {
        $(".disk").html(`${formatBytes(data['used'], 1)}/${formatBytes(data['total'], 1)}`)
    }
});
