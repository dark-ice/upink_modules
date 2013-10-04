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
    <p class="p8">${ o.account_id.full or '-' }, ${ o.account_id.address or '-' }, ЄДПРОУ ${ o.account_id.account_number }, тел. ${ o.account_id.phone or '-' }, <br/>P/p ${ o.account_id.bank_number } в ${ o.account_id.bank or '-' }, МФО ${ o.account_id.bik or '-' }, ІПН ${ o.account_id.inn or '-' }, № свідоцтва ${ o.account_id.kpp or '-' }</p>
    <p class="p8">Одержувач ${ o.bank_id.fullname or '-' }</p>
    <p class="p8">Платник той самий</p>

    <h3 class="center">Рахунок-фактура № ${ o.number or '-' }</h3>
    <h2 class="center">від ${ o.date_invoice or '-' } р.</h2>

    <table>
        <thead>
            <tr>
                <td>№</td>
                <td>Повна назва товару</td>
                <td>Од.вим.</td>
                <td>К-ть</td>
                <td>Ціна без ПДВ</td>
                <td>Сума без ПДВ</td>
            </tr>
        </thead>
        <tfoot>
        <tr>
            <td colspan="5" class="right">Разом без ПДВ:</td>
            <td class="right">${ o.untaxed }</td>
        </tr>
        <tr>
            <td colspan="5" class="right">ПДВ:</td>
            <td class="right">${ o.a_tax }</td>
        </tr>
        <tr>
            <td colspan="5" class="right">Всього з ПДВ:</td>
            <td class="right">${ o.a_total }</td>
        </tr>
        </tfoot>
        % for l in o.invoice_line:
            <tr>
                <td class="center">${ l.nbr }</td>
                <td>${ l.service_id.name }</td>
                <td class="right">1</td>
                <td class="right">шт.</td>
                <td class="right">${ get_total(l.price_currency, o.account_id.tax)[0] }</td>
                <td class="right">${ get_total(l.price_currency, o.account_id.tax)[0] }</td>
            </tr>
        % endfor
    </table>
    <p class="bold p8">Всього на суму:</p>
    <p class="bold p8">${ o.a_total }</p>
    <div style="position: relative;">
        <table class="footer">
            <tr>
                <td class="p8 bold">ПДВ: ${ o.a_tax }</td>
                <td class="p8 bold right">Виписав(ла)</td>
                <td class="p8 bold right" style="border-bottom: 1px solid black; width: 400px;"></td>
            </tr>
        </table>
        % if post == 'yes':
            <img src="data:image/png;base64,${ o.account_id.stamp }"  style="position: absolute; top: -50px; right: 50px; width: auto; height: 220px;" />
        % endif
    </div>
    <p class="p8 bold">Рахунок фактура дiйсна на протязi 3-x днiв.</p>
</body>
% endfor
</html>