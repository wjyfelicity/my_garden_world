class _Window:
    def __init__(self, title: str) -> None:
        self.title = title
        self.close_button_offset = (0.95, 0.05)
        # 右上角关闭按钮相对坐标，后续可以根据窗口类型微调；还可以用image recognition找到关闭按钮位置

    def rect(self) -> tuple[int, int, int, int]:
        # TODO: get the window rect by title, return (left, top, right, bottom)
        ...

    def close(self) -> None:
        # TODO: click the close button at top-right corner
        ...

    def is_open(self) -> bool:
        # TODO: check if the window is open
        ...

    def info(self) -> str:
        # TODO: get the content of the window, need OCR or image recognition
        ...


resident_order = _Window("居民订单")
pick_record = _Window("采摘记录")
pick_water_drop = _Window("领取水滴")
customer_order = _Window("顾客订单")
assemble_bouquet = _Window("制作花艺")
display_bouquet = _Window("售卖花艺")
collect_pearl = _Window("采集珍珠")
water_cart = _Window("水车介绍")
water_drop_bonus = _Window("大量水滴奖励")

windows = {
    "居民订单": resident_order,
    "采摘记录": pick_record,
    "领取水滴": pick_water_drop,
    "顾客订单": customer_order,
    "制作花艺": assemble_bouquet,
    "售卖花艺": display_bouquet,
    "采集珍珠": collect_pearl,
    "水车介绍": water_cart,
    "大量水滴奖励": water_drop_bonus,
}
