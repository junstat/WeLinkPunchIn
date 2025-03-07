// 文件路径：/sdcard/daka_schedule.json
const SCHEDULE_FILE = "/sdcard/daka_schedule.json";

function punchIn() {
    launchApp("WeLink");
    sleep(3000);

    let widget = text("业务").findOne();
    if (!widget) {
        toast("未找到业务选项卡，退出了.....");
        exit();
    }

    let bounds = widget.bounds();
    click(bounds.centerX(), bounds.centerY());

    for (let i = 0; i < 5; ++i) {
        let btn = text("打卡").findOne();
        if (!btn) {
            toast("未找到打卡按钮，退出了....");
            exit();
        }

        sleep(2000);
        let btnBounds = btn.bounds()
        click(btnBounds.centerX(), btnBounds.centerY());
    }
}

function isWednesdayOrFriday() {
    const today = new Date().getDay();
    return today === 3 || today === 5; // 3=周三,5=周五
}

// 生成指定范围内的随机分钟数
function randomMinutes(minHour, minMinute, maxHour, maxMinute) {
    let min = minHour * 60 + minMinute;
    let max = maxHour * 60 + maxMinute;
    return Math.floor(Math.random() * (max - min + 1)) + min;
}

// 转换分钟数为时间对象
function minutesToTime(totalMinutes) {
    return {
        hour: Math.floor(totalMinutes / 60),
        minute: totalMinutes % 60
    };
}

function generateSchedule() {
    // 上班时间 08:26~09:26
    let workTimeMinutes = randomMinutes(8, 26, 9, 26);

    // 下班时间 20:35~21:25
    let offTimeMinutes = isWednesdayOrFriday() ? randomMinutes(18, 35, 19, 25) :
        randomMinutes(20, 35, 21, 25);

    return {
        date: new Date().toDateString(),
        work: minutesToTime(workTimeMinutes),
        off: minutesToTime(offTimeMinutes),
        workDone: false,
        offDone: false
    };
}

function getSchedule() {
    if (!files.exists(SCHEDULE_FILE)) return generateSchedule();

    let saved = JSON.parse(files.read(SCHEDULE_FILE));
    if (saved.date !== new Date().toDateString()) {
        return generateSchedule();
    }
    return saved;
}

function saveSchedule(schedule) {
    files.write(SCHEDULE_FILE, JSON.stringify(schedule));
}

function main() {
    let schedule = getSchedule();
    let now = new Date();
    let currentMinutes = now.getHours() * 60 + now.getMinutes();

    toast(`上班打卡时间, ${schedule.work.hour}: ${schedule.work.minute}`);
    // 上班打卡逻辑
    if (!schedule.workDone && currentMinutes >= (schedule.work.hour * 60 + schedule.work.minute)) {
        sleep(3000);
        toast("开始上班打卡");
        punchIn();
        schedule.workDone = true;
    }

    toast(`下班打卡时间, ${schedule.off.hour}: ${schedule.off.minute}`);
    if (!schedule.offDone && currentMinutes >= (schedule.off.hour * 60 + schedule.off.minute)) {
        sleep(3000);
        punchIn();
        toast("开始下班打卡");
        schedule.offDone = true;
    }
    saveSchedule(schedule);
}

main();