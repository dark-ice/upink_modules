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

        .p6 {
            font-size: 6pt;
        }

        .p8 {
            font-size: 8pt;
        }

        .p10 {
            font-size: 10pt;
        }

        .p11 {
            font-size: 11pt;
        }

        .p14 {
            font-size: 14pt;
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
            text-align: center;
            vertical-align: top;
        }

        table td {
            border: 1px solid black;
        }

        table.header {
            border: none;
        }

        table tfoot td.b1 {
            border: none;
            border-bottom: 1px solid black;
        }

        table tfoot{
            border: none;
        }

        table tfoot td {
            border: none;
        }
    </style>

</head>
% for o in objects:
<body>
    <p class="center p11 bold">АКТ СВЕРКИ</p>
    <p class="center p8">взаимных расчетов за период: с ${ o.date_start } по ${ o.date_end }<br>
    между ${ o.account_id.full or '-' }<br>
    и ${ get_partner(o.bank_id)[2] or '-' }</p>

    <p class="p8">Мы, нижеподписавщиеся, Генеральный директор ${ o.account_id.full or '-' }, ${ o.account_id.responsible or '-' }, с одной стороны и ${ get_partner(o.bank_id)[2] or '-' }, с другой стороны, составили настоящий акт сверки в том, что состояние взаимных расчетов по данным учета следующее:</p>

    <table class="p8">
        <thead class="p18">
        <tr>
            <td colspan="4" width="50%">По данным ${ o.account_id.full or '-' }, ${ o.account_id.currency_id.symbol or '-' }.</td>
            <td colspan="4">По данным ${ get_partner(o.bank_id)[2] or '-' }, ${ o.account_id.currency_id.symbol or '-' }.</td>
        </tr>
        <tr>
            <td>№ п/п</td>
            <td>Наименование операции, документы</td>
            <td>Дебет</td>
            <td>Кредит</td>
            <td>№ п/п</td>
            <td>Наименование операции, документы</td>
            <td>Дебет</td>
            <td>Кредит</td>
        </tr>
        </thead>
        <tfoot>
        <tr>
            <td colspan="4" width="50%">По данным ${ o.account_id.full or '-' }</td>
            <td colspan="4"></td>
        </tr>
        <tr>
            <td colspan="4" width="50%">На ${ o.date_end }
                %if o.saldo < 0:
                    задолженноть в пользу ${ o.account_id.full or '-' } ${ (-1) * o.saldo} руб.
                %elif o.saldo > 0:
                    задолженность в пользу ${ get_partner(o.bank_id)[0] or '-' } ${ o.saldo} руб.
                %else:
                    задолженность отсутствует.
                %endif
            </td>
            <td colspan="4"></td>
        </tr>
        <tr>
            <td colspan="4" width="50%">От ${ o.account_id.full or '-' }</td>
            <td colspan="4">От ${ get_partner(o.bank_id)[2] or '-' }</td>
        </tr>
        <tr>
            <td colspan="4" width="50%">Генеральный директор</td>
            <td colspan="4">Генеральный директор</td>
        </tr>
        <tr style="height: 20px;">
            <td colspan="3" class="b1"></td>
            <td></td>
            <td colspan="4" class="b1"></td>
        </tr>
        <tr>
            <td colspan="3" class="top center">(${ o.account_id.responsible })</td>
            <td></td>
            <td colspan="4" class="top center">${ get_partner(o.bank_id)[1] or '-' }</td>
        </tr>
        <tr>
            <td colspan="4">М.П.</td>
            <td colspan="4">М.П.</td>
        </tr>
        </tfoot>
        <tr>
            <td class="right">1</td>
            <td>Сальдо на ${ o.date_start }</td>
            <td class="right">${o.prev_saldo if (o.prev_saldo < 0) else '0'}</td>
            <td class="right">${o.prev_saldo if (o.prev_saldo > 0) else '0'}</td>
            <td class="right">1</td>
            <td></td>
            <td></td>
            <td></td>
        </tr>
        % for l in o.act_ids:
            <tr>
                <td class="right">${ loop.index + 2 }</td>
                <td>${ l.line_type }</td>
                <td class="right">${l.line_cash * (-1) if (l.color_type == 'out') else '0'}</td>
                <td class="right">${l.line_cash if (l.color_type == 'in') else '0'}</td>
                <td class="right">${ loop.index + 2 }</td>
                <td></td>
                <td></td>
                <td></td>
            </tr>
        % endfor
        <tr>
            <td></td>
            <td>Обороты за период</td>
            <td class="right">${ o.debit }</td>
            <td class="right">${ o.credit }</td>
            <td></td>
            <td></td>
            <td></td>
            <td></td>
        </tr>
        <tr>
            <td></td>
            <td>Сальдо на ${ o.date_end }</td>
            <td class="right">${ o.saldo if (o.saldo <= 0) else '0'}</td>
            <td class="right">${ o.saldo if (o.saldo >= 0) else '0'}</td>
            <td></td>
            <td></td>
            <td></td>
            <td></td>
        </tr>
    </table>


</body>
% endfor
</html>