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
            border: 1px solid black;
            width: 100%;
            border-collapse: collapse;
            border-spacing: 0;
            empty-cells: show;
        }

        table thead td {
            font-weight: bold;
            text-align: center;
        }

        table td {
            border: 1px solid black;
        }

        table.footer td {
            border: none;
        }
    </style>

</head>
% for o in objects:
<body>
    <p class="p8 bold center">${ o.invoice_id.account_id.full or '-' }</p>
    <p class="p8 center">ИНН ${ o.invoice_id.account_id.inn or '-' }, КПП ${ o.invoice_id.account_id.kpp or '-' }, ${ o.invoice_id.account_id.address or '-' }, тел.: ${ o.invoice_id.account_id.phone or '-' }</p>
    <h2 class="center">АКТ № ${ o.id or '-' } от ${ o.document_date or '-' }</h2>
    <p class="p8 center">${ o.invoice_id.bank_id.fullname or '-' }</p>
    <p class="p8 center">${ get_client_info(o.invoice_id.bank_id.id) or '-'}</p>

    <table class="p8">
        <thead>
        <tr>
            <td>№</td>
            <td>Наименование работы(услуги)</td>
            <td>Ед. изм.</td>
            <td>Количество</td>
            <td>Цена</td>
            <td>Сумма, руб.</td>
        </tr>
        </thead>
        <tfoot>
        <tr>
            <td colspan="2" style="border: none;"></td>
            <td colspan="3" class="p8 bold center">Итого:</td>
            <td class="p8 right">${ get_total(o.document_cash, o.invoice_id.tax)[0] }</td>
        </tr>
        <tr>
            <td colspan="2" style="border: none;"></td>
            <td colspan="3" class="p8 center">НДС:</td>
            <td class="p8 right">${ get_total(o.document_cash, o.invoice_id.tax)[1] }</td>
        </tr>
        <tr>
            <td colspan="2" style="border: none;"></td>
            <td colspan="3" class="p8 bold center">Всего с учетом НДС:</td>
            <td class="p8 right">${ o.document_cash }</td>
        </tr>
        </tfoot>
        % for l in o.document_line_id:
            <tr>
                <td class="center">${ l.nbr }</td>
                <td>${ l.service_id.name }</td>
                <td class="right">шт.</td>
                <td class="right">1.00</td>
                <td class="right">${ l.name }</td>
                <td class="right">${ l.name }</td>
            </tr>
        % endfor
    </table>
        
    <p class="p8 center">Всего оказано услуг на сумму: ${ get_word_cash(o.document_cash)[0] } ${ get_word_cash(o.document_cash)[1] }.</>
    <p class="p8 center bold">в т.ч.: НДС - ${ get_word_cash(get_total(o.document_cash, o.invoice_id.tax)[1])[0] } ${ get_word_cash(get_total(o.document_cash, o.invoice_id.tax)[1])[1] }.</p>

    <p class="p8 center">Вышеперечисленные услуги выполнены полностью и в срок. Заказчик претензий по объему, качеству и
срокам оказания услуг не имеет.</p>

    <table class="footer p8" style="border: none;">
        <tr>
            <td width="50%">Исполнитель</td>
            <td>Заказчик</td>
        </tr>
        <tr>
            <td style="padding-left: 100px;">Подпись</td>
            <td style="padding-left: 100px;">Подпись</td>
        </tr>
        <tr>
            <td style="padding-left: 110px;">М.П.</td>
            <td style="padding-left: 110px;">М.П.</td>
        </tr>
    </table>
</body>
% endfor
</html>