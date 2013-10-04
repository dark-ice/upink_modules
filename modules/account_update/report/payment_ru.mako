<html>
<head>
    <style type="text/css">
        body {
            background: #fff;
            margin: 0;
            padding: 0;
        }

        .center {
            text-align: center;
        }

        .right {
            text-align: right;
        }

        .top {
             vertical-align: top;
        }

        .bottom {
             vertical-align: bottom;
        }

        .p8 {
            font-size: 8pt;
        }

        .p14 {
            font-size: 8pt;
        }

        .bold {
            font-weight: bold;
        }

        table {
            border: none;
            width: 100%;
            border-collapse: collapse;
            border-spacing: 0;
            empty-cells: show;
        }

        table thead td {
            font-weight: bold;
            text-align: center;
        }

        table tfoot tr:first-child{
            height: 42px;
        }

        table tfoot tr:first-child td {
            vertical-align: bottom;
        }

        table tfoot td {
            border: none;
            height: 20px;
        }

        table td {
            border: 1px solid black;
            height: 30px;
        }

        table.footer td {
            border: none;
        }
    </style>

</head>
% for o in objects:
<body>
    <p class="p8 center">Внимание! Оплата данного счета означает согласие с условиями поставки товара. Уведомление об оплате
обязательно, в противном случае не гарантируется наличие товара на складе. Товар отпускается по факту
прихода денег на р/с Поставщика, самовывозом, при наличии доверенности и паспорта.</p>
    <p class="p8 center">Счет действителен в течение 3-х банковских дней</p>

    <table>
        <tr>
            <td colspan="4" rowspan="2" style="height: 60px;  vertical-align: top;">${ o.account_id.bank or '-' }</td>
            <td>БИК</td>
            <td>${ o.account_id.bik or '-' }</td>
        </tr>
        <tr>
            <td rowspan="2" style="height: 60px; width: 60px; vertical-align: top;">Сч. №</td>
            <td rowspan="2" style="height: 60px; vertical-align: bottom;">${ o.account_id.bank_number or '-' }</td>
        </tr>
        <tr>
            <td colspan="4">Банк получателя</td>
        </tr>
        <tr>
            <td>ИНН</td>
            <td>${ o.account_id.inn or '-' }</td>
            <td>КПП</td>
            <td>${ o.account_id.kpp or '-' }</td>
            <td rowspan="3" style="vertical-align: top; width: 60px;">Сч. №</td>
            <td rowspan="3" style="vertical-align: bottom;">${ o.account_id.account_number or '-' }</td>
        </tr>
        <tr>
            <td colspan="4">${ o.account_id.full or '-' }</td>
        </tr>
        <tr>
            <td colspan="4">Получатель</td>
        </tr>
    </table>

    <h2 class="center">Счет на оплату № ${ o.number or '-' } от ${ get_date(o.date_invoice) or '-' } г.</h2>
    <p class="p8 bold">Поставщик: ${ o.account_id.full or '-' }, ИНН ${ o.account_id.inn or '-' }, КПП ${ o.account_id.kpp or '-' }, ${ o.account_id.address or '-' }, тел.: ${ o.account_id.phone or '-' }</p>
    <p class="p8 bold">Покупатель: ${ o.bank_id.fullname or '-' }, ${ get_client_info(o.bank_id.id) or '-'}</p>

    <table>
        <thead>
            <tr>
                <td>№</td>
                <td>Товары (работы, услуги)</td>
                <td>Кол-во</td>
                <td>Ед.</td>
                <td>Цена</td>
                <td style="width: 80px">Сумма без скидки</td>
                <td style="width: 80px">Скидка (наценка)</td>
                <td>Сумма</td>
            </tr>
        </thead>
        <tfoot>
        <tr>
            <td colspan="5" class="bold right">Итого:</td>
            <td class="right">${ o.a_total }</td>
            <td class="right">0.00</td>
            <td class="right">${ o.a_total }</td>
        </tr>
        <tr>
            <td colspan="5" class="bold right">В том числе НДС:</td>
            <td></td>
            <td></td>
            <td class="right">${ o.a_tax }</td>
        </tr>
        <tr>
            <td colspan="5" class="bold right">Всего к оплате:</td>
            <td></td>
            <td></td>
            <td class="right">${ o.a_total }</td>
        </tr>
        </tfoot>
        % for l in o.invoice_line:
            <tr>
                <td class="center">${ l.nbr }</td>
                <td>${ l.service_id.name }</td>
                <td class="right">шт.</td>
                <td class="right">1</td>
                <td class="right">${ l.price_currency}</td>
                <td class="right">${ l.price_currency}</td>
                <td class="right">0.00</td>
                <td class="right">${ l.price_currency}</td>
            </tr>
        % endfor
    </table>

    <div style="position: relative;">
        <table class="footer" border="1">
            <tr>
                <td colspan="2" class="p8">Всего наименований</td>
                <td class="p8 center bold" style="width: 80px;">${ get_len(o.invoice_line) }</td>
                <td>на сумму</td>
                <td class="p8 center"><span style="font-weight: bold">${ o.a_total }</span> руб.</td>
            </tr>
            <tr style="border-bottom: 1px solid black" class="bottom">
                <td colspan="5" class="p8 bold">${ get_word_cash(o.a_total)[0] } ${ get_word_cash(o.a_total)[1] }</td>
            </tr>
            <tr style="border-bottom: 1px solid black; height: 30px;" class="bottom">
                <td class="p8 bold">Руководитель</td>
                <td class="p8 bold center">Генеральный директор</td>
                <td></td>
                <td></td>
                <td class="p8 bold right">${ o.account_id.responsible }</td>
            </tr>
            <tr class="top p8">
                <td></td>
                <td style="padding-left: 120px;">должность</td>
                <td></td>
                <td class="center">подпись</td>
                <td class="right" style="padding-right: 40px;">расшифровка подписи</td>
            </tr>
            <tr style="border-bottom: 1px solid black;" class="bottom">
                <td colspan="4" class="p8 bold">Главный (старший) бухгалтер</td>
                <td class="p8 bold right">${ o.account_id.responsible }</td>
            </tr>
            <tr class="top p8">
                <td colspan="3"></td>
                <td class="center">подпись</td>
                <td class="right" style="padding-right: 40px;">расшифровка подписи</td>
            </tr>
        </table>
        % if post == 'yes':
            <img src="data:image/png;base64,${ o.account_id.stamp }"  style="position: absolute; top: -40px; right: 50px; width: 288px; height: 220px;" />
        % endif
    </div>

    
</body>
% endfor
</html>